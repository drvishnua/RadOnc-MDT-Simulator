import { spawn, execFileSync } from "node:child_process";
import { access, mkdtemp, readFile, rm } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import process from "node:process";

const APP_URL = "http://127.0.0.1:5173/";
const API_URL = "http://127.0.0.1:8000";
const TEST_TIMEOUT_MS = 20_000;

const edgeCandidates = [
  process.env["PROGRAMFILES(X86)"] && path.join(process.env["PROGRAMFILES(X86)"], "Microsoft", "Edge", "Application", "msedge.exe"),
  process.env.PROGRAMFILES && path.join(process.env.PROGRAMFILES, "Microsoft", "Edge", "Application", "msedge.exe")
].filter(Boolean);

let edgePath = null;
for (const candidate of edgeCandidates) {
  try {
    await access(candidate);
    edgePath = candidate;
    break;
  } catch {
    // Try the next standard Edge installation path.
  }
}
if (!edgePath) throw new Error("Microsoft Edge was not found; the registry browser regression cannot run.");

const token = new Date().toISOString().replace(/[-:.TZ]/g, "").slice(0, 14) + "-" + Math.random().toString(16).slice(2, 8);
const originalName = "E2E Browser Patient " + token;
const updatedName = "E2E Browser Patient Updated " + token;
const originalTitle = "Browser registry regression " + token;
const updatedTitle = originalTitle + " updated";
const originalSummary = "Browser workflow version one " + token + ". This disposable fictional training summary verifies patient persistence and historical restoration.";
const updatedSummary = "Browser workflow version two " + token + ". This edited fictional training summary verifies immutable case version history.";

const tempRoot = await mkdtemp(path.join(os.tmpdir(), "radonc-patient-registry-e2e-"));
const profileDir = path.join(tempRoot, "edge-profile");
const activeRequests = new Map();
let edgeProcess = null;
let socket = null;
let commandId = 0;
let patientIdentifier = null;
let patientId = null;

function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function waitUntil(check, description, timeoutMs = TEST_TIMEOUT_MS) {
  const deadline = Date.now() + timeoutMs;
  let lastError = null;
  while (Date.now() < deadline) {
    try {
      const value = await check();
      if (value) return value;
    } catch (error) {
      lastError = error;
    }
    await delay(250);
  }
  throw new Error("Timed out waiting for " + description + (lastError ? ": " + lastError.message : ""));
}

async function waitForDevToolsPort() {
  const activePortFile = path.join(profileDir, "DevToolsActivePort");
  return waitUntil(async () => {
    const value = await readFile(activePortFile, "utf8").catch(() => "");
    const port = Number(value.split(/\r?\n/)[0]);
    return Number.isInteger(port) && port > 0 ? port : null;
  }, "Edge DevTools endpoint", 15_000);
}

async function connectToPage(port) {
  const targets = await waitUntil(async () => {
    const response = await fetch("http://127.0.0.1:" + port + "/json/list");
    if (!response.ok) return null;
    const items = await response.json();
    return items.find(item => item.type === "page" && item.url.startsWith(APP_URL)) ?? null;
  }, "the Vite page target", 15_000);

  socket = new WebSocket(targets.webSocketDebuggerUrl);
  await new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error("Timed out connecting to Edge DevTools.")), 10_000);
    socket.addEventListener("open", () => {
      clearTimeout(timer);
      resolve();
    }, { once: true });
    socket.addEventListener("error", () => {
      clearTimeout(timer);
      reject(new Error("Could not connect to the Edge DevTools WebSocket."));
    }, { once: true });
  });

  socket.addEventListener("message", event => {
    let message;
    try {
      message = JSON.parse(String(event.data));
    } catch {
      return;
    }
    if (!message.id) return;
    const pending = activeRequests.get(message.id);
    if (!pending) return;
    activeRequests.delete(message.id);
    if (message.error) pending.reject(new Error(message.error.message || "DevTools command failed."));
    else pending.resolve(message.result);
  });

  await sendCommand("Page.enable");
  await sendCommand("Runtime.enable");
}

function sendCommand(method, params = {}) {
  if (!socket || socket.readyState !== WebSocket.OPEN) {
    return Promise.reject(new Error("The Edge DevTools connection is not open."));
  }
  const id = ++commandId;
  return new Promise((resolve, reject) => {
    activeRequests.set(id, { resolve, reject });
    socket.send(JSON.stringify({ id, method, params }));
    setTimeout(() => {
      const pending = activeRequests.get(id);
      if (pending) {
        activeRequests.delete(id);
        pending.reject(new Error("DevTools command timed out: " + method));
      }
    }, 12_000).unref?.();
  });
}

async function evaluate(expression) {
  const result = await sendCommand("Runtime.evaluate", {
    expression,
    awaitPromise: true,
    returnByValue: true,
    userGesture: true
  });
  if (result.exceptionDetails) {
    throw new Error(result.exceptionDetails.exception?.description || result.exceptionDetails.text || "Browser JavaScript evaluation failed.");
  }
  return result.result?.value;
}

async function waitForExpression(expression, description, timeoutMs = TEST_TIMEOUT_MS) {
  return waitUntil(async () => await evaluate(expression), description, timeoutMs);
}

function json(value) {
  return JSON.stringify(value);
}

async function setLabelValue(labelText, value, elementSelector = "input, textarea") {
  const expression =
    "(() => {" +
    "const label = [...document.querySelectorAll('label')].find(node => (node.innerText || '').trim().startsWith(" + json(labelText) + "));" +
    "const element = label && label.querySelector(" + json(elementSelector) + ");" +
    "if (!element) throw new Error('Could not find field: ' + " + json(labelText) + ");" +
    "const prototype = element instanceof HTMLTextAreaElement ? HTMLTextAreaElement.prototype :" +
      "element instanceof HTMLSelectElement ? HTMLSelectElement.prototype : HTMLInputElement.prototype;" +
    "const setter = Object.getOwnPropertyDescriptor(prototype, 'value').set;" +
    "setter.call(element, " + json(value) + ");" +
    "element.dispatchEvent(new Event('input', { bubbles: true }));" +
    "element.dispatchEvent(new Event('change', { bubbles: true }));" +
    "return element.value;" +
    "})()";
  return evaluate(expression);
}

async function selectOptionByText(labelText, optionText) {
  const expression =
    "(() => {" +
    "const label = [...document.querySelectorAll('label')].find(node => (node.innerText || '').trim().startsWith(" + json(labelText) + "));" +
    "const element = label && label.querySelector('select');" +
    "if (!element) throw new Error('Could not find select: ' + " + json(labelText) + ");" +
    "const option = [...element.options].find(item => (item.textContent || '').includes(" + json(optionText) + "));" +
    "if (!option) throw new Error('Could not find option: ' + " + json(optionText) + ");" +
    "const setter = Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, 'value').set;" +
    "setter.call(element, option.value);" +
    "element.dispatchEvent(new Event('change', { bubbles: true }));" +
    "return option.value;" +
    "})()";
  return evaluate(expression);
}

async function clickButton(textPrefix) {
  const expression =
    "(() => {" +
    "const button = [...document.querySelectorAll('button')].find(node => (node.innerText || '').trim().startsWith(" + json(textPrefix) + "));" +
    "if (!button) throw new Error('Could not find button: ' + " + json(textPrefix) + ");" +
    "if (button.disabled) throw new Error('Button is disabled: ' + " + json(textPrefix) + ");" +
    "button.click();" +
    "return true;" +
    "})()";
  await evaluate(expression);
}

async function assertFieldValue(labelText, expectedValue) {
  const expression =
    "(() => {" +
    "const label = [...document.querySelectorAll('label')].find(node => (node.innerText || '').trim().startsWith(" + json(labelText) + "));" +
    "const element = label && label.querySelector('input, textarea');" +
    "return !!element && element.value === " + json(expectedValue) + ";" +
    "})()";
  const ok = await waitForExpression(expression, "the " + labelText + " field to match its saved value");
  if (!ok) throw new Error("The " + labelText + " field did not restore the expected value.");
}

async function readPatientOption(name) {
  return evaluate(
    "(() => {" +
    "const label = [...document.querySelectorAll('label')].find(node => (node.innerText || '').trim().startsWith('Registered patient'));" +
    "const select = label && label.querySelector('select');" +
    "const option = select && [...select.options].find(item => (item.textContent || '').includes(" + json(name) + "));" +
    "if (!option) return null;" +
    "const match = (option.textContent || '').match(/RAD-\\d{6}/);" +
    "return match ? { value: option.value, identifier: match[0], text: option.textContent } : null;" +
    "})()"
  );
}

async function verifyBackendDeletion() {
  const patientsResponse = await fetch(API_URL + "/api/patients");
  if (!patientsResponse.ok) throw new Error("The patient registry API could not be checked during cleanup.");
  const body = await patientsResponse.json();
  const matches = (body.patients || []).filter(patient =>
    patient.patient_name === originalName || patient.patient_name === updatedName
  );
  for (const patient of matches) {
    await fetch(API_URL + "/api/patients/" + patient.patient_id, { method: "DELETE" });
  }
}

try {
  edgeProcess = spawn(edgePath, [
    "--headless=new",
    "--remote-debugging-port=0",
    "--remote-debugging-address=127.0.0.1",
    "--no-first-run",
    "--no-default-browser-check",
    "--disable-gpu",
    "--disable-extensions",
    "--disable-background-networking",
    "--disable-sync",
    "--window-size=1440,1100",
    "--user-data-dir=" + profileDir,
    APP_URL
  ], { stdio: "ignore", windowsHide: true });

  edgeProcess.on("exit", code => {
    if (code !== null && code !== 0) console.error("Edge exited with code " + code);
  });

  const port = await waitForDevToolsPort();
  await connectToPage(port);
  await waitForExpression("!!document.querySelector('.app-shell')", "React application mount");
  await waitForExpression(
    "(() => { const label = [...document.querySelectorAll('label')].find(node => (node.innerText || '').trim().startsWith('Registered patient')); return !!label && !!label.querySelector('select'); })()",
    "the patient registry selector"
  );

  await setLabelValue("Fictional patient name", originalName);
  await setLabelValue("Diagnosis / MDT case title", originalTitle);
  await setLabelValue("Clinical summary", originalSummary);
  await clickButton("Validate patient details");
  await waitForExpression(
    "[...document.querySelectorAll('.result-card')].some(node => (node.innerText || '').includes('Case structure valid'))",
    "case validation to complete"
  );
  await clickButton("Register new patient");

  const firstOption = await waitUntil(() => readPatientOption(originalName), "the newly registered patient in the registry");
  patientIdentifier = firstOption.identifier;
  patientId = firstOption.value;
  await waitForExpression(
    "document.body.innerText.includes('Loaded patient: " + patientIdentifier + "')",
    "the newly registered patient to load"
  );
  await assertFieldValue("Fictional patient name", originalName);
  await assertFieldValue("Clinical summary", originalSummary);

  await sendCommand("Page.reload", { ignoreCache: true });
  await waitForExpression("!!document.querySelector('.app-shell')", "the application after browser refresh");
  await waitUntil(() => readPatientOption(originalName), "the saved patient after browser refresh");
  await selectOptionByText("Registered patient", originalName);
  await clickButton("Load patient");
  await waitForExpression(
    "document.body.innerText.includes('Loaded patient: " + patientIdentifier + "')",
    "the saved patient to reload from the registry"
  );
  await assertFieldValue("Fictional patient name", originalName);
  await assertFieldValue("Clinical summary", originalSummary);

  await setLabelValue("Fictional patient name", updatedName);
  await setLabelValue("Clinical summary", updatedSummary);
  await clickButton("Validate patient details");
  await waitForExpression(
    "[...document.querySelectorAll('button')].some(node => (node.innerText || '').trim().startsWith('Save new version of " + patientIdentifier + "') && !node.disabled)",
    "the version-save action after editing"
  );
  await clickButton("Save new version of " + patientIdentifier);
  await waitForExpression(
    "(() => { const label = [...document.querySelectorAll('label')].find(node => (node.innerText || '').trim().startsWith('Saved case version')); return !!label && !!label.querySelector('select') && [...label.querySelector('select').options].some(option => (option.textContent || '').includes('Version 2 ·')); })()",
    "the second immutable case version"
  );
  await waitForExpression(
    "document.body.innerText.includes('Loaded patient: " + patientIdentifier + " · 2 immutable case version(s)')",
    "the patient detail to report both immutable versions"
  );
  await assertFieldValue("Fictional patient name", updatedName);
  await assertFieldValue("Clinical summary", updatedSummary);

  await selectOptionByText("Saved case version", "Version 1 ·");
  await clickButton("Load version");
  await assertFieldValue("Fictional patient name", originalName);
  await assertFieldValue("Clinical summary", originalSummary);
  const restoredVersionSelected = await evaluate(
    "(() => { const label = [...document.querySelectorAll('label')].find(node => (node.innerText || '').trim().startsWith('Saved case version')); const select = label && label.querySelector('select'); const option = select && [...select.options].find(item => (item.textContent || '').includes('Version 1 ·')); return !!option && select.value === option.value; })()"
  );
  if (!restoredVersionSelected) throw new Error("The registry did not retain Version 1 as the active restored version.");
  await waitForExpression(
    "(() => { const label = [...document.querySelectorAll('label')].find(node => (node.innerText || '').trim().startsWith('Saved case version')); return !!label && [...label.querySelector('select').options].some(option => (option.textContent || '').includes('Version 2 ·')); })()",
    "the preserved second version after restoring version one"
  );

  await evaluate("window.confirm = () => true");
  await clickButton("Delete patient and linked results");
  await waitForExpression(
    "!document.body.innerText.includes('Loaded patient: " + patientIdentifier + "')",
    "the test patient to be removed from the loaded form"
  );
  await waitForExpression(
    "(() => { const label = [...document.querySelectorAll('label')].find(node => (node.innerText || '').trim().startsWith('Registered patient')); return !!label && ![...label.querySelector('select').options].some(option => (option.textContent || '').includes(" + json(patientIdentifier) + ")); })()",
    "the deleted patient to disappear from the registry selector"
  );

  const deletedLookup = await fetch(API_URL + "/api/patients/" + patientId);
  if (deletedLookup.status !== 404) throw new Error("The deleted patient detail endpoint did not return HTTP 404.");

  console.log("PATIENT_REGISTRY_BROWSER_E2E_OK");
  console.log("Verified in headless Edge: create, reload, edit, save immutable version 2, restore version 1, and delete.");
  console.log("Disposable registry identifier: " + patientIdentifier);
} finally {
  await verifyBackendDeletion().catch(error => console.error("Cleanup warning: " + error.message));
  for (const pending of activeRequests.values()) pending.reject(new Error("Browser test ended."));
  activeRequests.clear();
  try {
    if (socket && socket.readyState === WebSocket.OPEN) socket.close();
  } catch {
    // The Edge process may already have exited.
  }
  if (edgeProcess?.pid && process.platform === "win32") {
    try {
      execFileSync("taskkill", ["/PID", String(edgeProcess.pid), "/T", "/F"], { stdio: "ignore" });
    } catch {
      // Browser shutdown is best-effort after the isolated profile is no longer needed.
    }
  } else if (edgeProcess && !edgeProcess.killed) {
    edgeProcess.kill("SIGTERM");
  }
  await rm(tempRoot, { recursive: true, force: true }).catch(() => {});
}
