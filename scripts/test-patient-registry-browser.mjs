import { spawn, execFileSync } from "node:child_process";
import { access, mkdtemp, readFile, rm } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const SCRIPT_DIR = path.dirname(fileURLToPath(import.meta.url));
const SOURCE_ROOT = path.dirname(SCRIPT_DIR);
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
const originalTitle = "Browser registry regression " + token;
const originalSummary = "Browser workflow version one " + token + ". This disposable fictional training summary verifies patient persistence and historical restoration.";
const updatedSummary = "Browser workflow version two " + token + ". This edited fictional training summary verifies immutable case version history.";
const structuredFieldValues = [
  ["Age (optional)", "63"],
  ["Primary site", "TEST_ONLY_PRIMARY_SITE"],
  ["Histology", "TEST_ONLY_HISTOLOGY"],
  ["Sex at birth", "TEST_ONLY_SEX_AT_BIRTH"],
  ["Performance status", "TEST_ONLY_PERFORMANCE_STATUS"],
  ["Clinical T stage", "TEST_ONLY_T_STAGE"],
  ["Clinical N stage", "TEST_ONLY_N_STAGE"],
  ["Clinical M stage", "TEST_ONLY_M_STAGE"],
  ["Stage group", "TEST_ONLY_STAGE_GROUP"],
  ["Pathology summary", "TEST_ONLY_PATHOLOGY_SUMMARY"],
  ["Imaging summary", "TEST_ONLY_IMAGING_SUMMARY"],
  ["Current medications", "TEST_ONLY_MEDICATION_A\nTEST_ONLY_MEDICATION_B"],
  ["Known allergies", "TEST_ONLY_ALLERGY_A"],
  ["Relevant investigations", "TEST_ONLY_INVESTIGATION_A\nTEST_ONLY_INVESTIGATION_B"],
  ["Relevant comorbidities", "TEST_ONLY_COMORBIDITY_A"],
  ["Prior treatment", "TEST_ONLY_PRIOR_TREATMENT_A"],
  ["Patient goals", "TEST_ONLY_PATIENT_STATED_GOAL_A"],
  ["Social context", "TEST_ONLY_SOCIAL_CONTEXT_A"],
  ["Resource context", "TEST_ONLY_RESOURCE_CONTEXT_A"],
  ["Known unknowns", "TEST_ONLY_UNKNOWN_A\nTEST_ONLY_UNKNOWN_B"]
];

const tempRoot = await mkdtemp(path.join(os.tmpdir(), "radonc-patient-registry-e2e-"));
const profileDir = path.join(tempRoot, "edge-profile");
const activeRequests = new Map();
let edgeProcess = null;
let socket = null;
let commandId = 0;
let patientIdentifier = null;
let patientId = null;
let dashboardPatientId = null;
let dashboardRunId = null;
let browserWorkflowCompleted = false;

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

async function waitForValidationReady() {
  await waitForExpression(
    "(() => { const button = [...document.querySelectorAll('button')].find(node => (node.innerText || '').trim().startsWith('Validate patient details')); return !!button && !button.disabled; })()",
    "backend connectivity and the case-validation form to become ready"
  );
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

async function clickDevelopmentMonitorRefresh() {
  const clicked = await evaluate(
    "(() => {" +
      "const panel = [...document.querySelectorAll('section')].find(node => node.getAttribute('aria-label') === 'Development Monitor');" +
      "const button = [...(panel?.querySelectorAll('button') || [])].find(node => (node.innerText || '').trim().startsWith('Refresh'));" +
      "if (!button) throw new Error('Could not find the Development Monitor refresh button.');" +
      "if (button.disabled) throw new Error('The Development Monitor refresh button is disabled.');" +
      "button.click();" +
      "return true;" +
    "})()"
  );
  if (!clicked) throw new Error("Development Monitor refresh button was not activated.");
}

async function setAllStructuredFieldValues() {
  await evaluate(
    "(() => { const section = document.querySelector('details.structured-fields'); if (!section) throw new Error('Structured case details section is missing.'); section.open = true; return true; })()"
  );
  for (const [label, value] of structuredFieldValues) {
    await setLabelValue(label, value);
  }
}

async function assertAllStructuredFieldValues() {
  // Labels inside a closed <details> element have no rendered innerText.
  // Open the structured section before using the same label-based field checks.
  await evaluate(
    "(() => { const section = document.querySelector('details.structured-fields'); if (!section) throw new Error('Structured case details section is missing.'); section.open = true; return true; })()"
  );
  for (const [label, value] of structuredFieldValues) {
    await assertFieldValue(label, value);
  }
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
    patient.patient_name === originalName
  );
  for (const patient of matches) {
    await fetch(API_URL + "/api/patients/" + patient.patient_id, { method: "DELETE" });
  }
}

async function verifyFourRoundDashboard() {
  const pythonExecutable = path.join(
    SOURCE_ROOT,
    "backend",
    ".venv",
    "Scripts",
    "python.exe"
  );
  const seedScript = path.join(SCRIPT_DIR, "seed-mdt-dashboard-e2e.py");
  const dashboardFixtureName = "Disposable dashboard E2E " + token;
  const seedMarker = execFileSync(
    pythonExecutable,
    [seedScript, dashboardFixtureName],
    {
      cwd: path.join(SOURCE_ROOT, "backend"),
      encoding: "utf8",
      windowsHide: true
    }
  );
  if (seedMarker.trim() !== "DASHBOARD_E2E_SEED_CREATED") {
    throw new Error("The dashboard fixture seeder returned an unexpected status marker.");
  }
  const registryResponse = await fetch(API_URL + "/api/patients");
  if (!registryResponse.ok) throw new Error("The disposable dashboard fixture could not be found in the patient registry.");
  const registryBody = await registryResponse.json();
  const fixturePatients = (registryBody.patients || []).filter(
    patient => patient.patient_name === dashboardFixtureName
  );
  if (fixturePatients.length !== 1) {
    throw new Error("Expected exactly one uniquely named disposable dashboard patient.");
  }
  dashboardPatientId = fixturePatients[0].patient_id;
  const detailResponse = await fetch(API_URL + "/api/patients/" + dashboardPatientId);
  if (!detailResponse.ok) throw new Error("The disposable dashboard patient detail could not be retrieved.");
  const dashboardPatient = await detailResponse.json();
  const fixtureVersionId = dashboardPatient.versions?.[0]?.case_version_id;
  const fixtureRuns = (dashboardPatient.runs || []).filter(
    run => run.case_version_id === fixtureVersionId
  );
  if (!fixtureVersionId || fixtureRuns.length !== 1) {
    throw new Error("Expected exactly one saved dashboard run for the disposable case version.");
  }
  dashboardRunId = fixtureRuns[0].run_id;

  const summaryResponse = await fetch(API_URL + "/api/runs/" + dashboardRunId);
  if (!summaryResponse.ok) {
    throw new Error("The seeded four-round dashboard run could not be retrieved.");
  }
  const savedSummary = await summaryResponse.json();
  if (
    savedSummary.completed_count !== 45 ||
    savedSummary.failed_count !== 0 ||
    savedSummary.status !== "completed"
  ) {
    throw new Error("The seeded R1 summary does not contain 45 completed contributions.");
  }

  await evaluate(
    "window.localStorage.setItem('radonc-mdt-active-batch', " +
      json(JSON.stringify(savedSummary)) +
      "); window.location.reload(); true"
  );
  await waitForExpression(
    "!!document.querySelector('.app-shell')",
    "the dashboard after restoring the saved four-round run"
  );

  await waitForExpression(
    "!!document.querySelector('.mission-control-panel') && " +
      "document.querySelectorAll('.mission-run-card').length > 0",
    "the read-only Mission Control panel and recent saved runs"
  );
  const missionControlSnapshot = await evaluate(
    "(() => {" +
      "const shortId = " + json(dashboardRunId.slice(0, 8)) + ";" +
      "const card = [...document.querySelectorAll('.mission-run-card')].find(node => (node.innerText || '').includes('Run ' + shortId));" +
      "if (!card) return { found: false, stages: [] };" +
      "const stages = [...card.querySelectorAll('.mission-round-card')].map(node => (node.innerText || '').replace(/\\s+/g, ' ').trim());" +
      "return { found: true, stages, hasSnapshot: (card.innerText || '').includes('Snapshot SHA-256') };" +
    "})()"
  );
  if (
    !missionControlSnapshot.found ||
    missionControlSnapshot.stages.length !== 4 ||
    !missionControlSnapshot.stages[0].includes("45/45 complete") ||
    !missionControlSnapshot.stages[1].includes("45/45 complete") ||
    !missionControlSnapshot.stages[2].includes("45/45 complete") ||
    !missionControlSnapshot.stages[3].includes("1/1 complete") ||
    !missionControlSnapshot.hasSnapshot
  ) {
    throw new Error("Mission Control did not render the seeded run's four persisted stage summaries: " + JSON.stringify(missionControlSnapshot));
  }
  console.log("MISSION_CONTROL_BROWSER_E2E_OK");
  console.log("Verified in headless Edge: the seeded run appears with R1/R2/R3 45/45 and Chair R4 1/1 completion counts and a case-snapshot hash prefix.");

  const r2Opened = await evaluate(
    "(() => {" +
      "const shortId = " + json(dashboardRunId.slice(0, 8)) + ";" +
      "const run = [...document.querySelectorAll('.mission-run-card')].find(node => (node.innerText || '').includes('Run ' + shortId));" +
      "const round = run?.querySelectorAll('.mission-round-card')[1];" +
      "const button = round?.querySelector('.mission-role-toggle');" +
      "if (button) button.click();" +
      "return !!button;" +
    "})()"
  );
  if (!r2Opened) throw new Error("Mission Control R2 role expansion button was not found.");
  await waitForExpression(
    "!!document.querySelector('.mission-role-detail') && document.querySelectorAll('.mission-role-row').length === 45",
    "all 45 R2 persisted role rows"
  );
  const r2Detail = await evaluate(
    "(() => {" +
      "const rows = [...document.querySelectorAll('.mission-role-row')];" +
      "return { count: rows.length, first: rows[0]?.innerText || '', leaksProse: (document.querySelector('.mission-role-detail')?.innerText || '').includes('provisional conclusion') };" +
    "})()"
  );
  if (r2Detail.count !== 45 || !r2Detail.first.includes("RO-01") || !r2Detail.first.toLowerCase().includes("completed") || r2Detail.leaksProse) {
    throw new Error("R2 role detail did not show 45 completed metadata-only rows: " + JSON.stringify(r2Detail));
  }

  const r4Opened = await evaluate(
    "(() => {" +
      "const shortId = " + json(dashboardRunId.slice(0, 8)) + ";" +
      "const run = [...document.querySelectorAll('.mission-run-card')].find(node => (node.innerText || '').includes('Run ' + shortId));" +
      "const round = run?.querySelectorAll('.mission-round-card')[3];" +
      "const button = round?.querySelector('.mission-role-toggle');" +
      "if (button) button.click();" +
      "return !!button;" +
    "})()"
  );
  if (!r4Opened) throw new Error("Mission Control R4 role expansion button was not found.");
  await waitForExpression(
    "document.querySelectorAll('.mission-role-row').length === 1",
    "the single R4 Chair role row"
  );
  const r4Detail = await evaluate(
    "(() => document.querySelector('.mission-role-row')?.innerText || '')()"
  );
  if (!r4Detail.includes("SG-07") || !r4Detail.toLowerCase().includes("completed")) {
    throw new Error("R4 drill-down did not show the completed Chair role only: " + r4Detail);
  }
  console.log("MISSION_CONTROL_ROLE_DRILLDOWN_E2E_OK");
  console.log("Verified in headless Edge: R2 exposes 45 persisted metadata-only role states; R4 exposes only the completed SG-07 Chair.");

  // Assert the separate GitHub development-process panel using the deterministic
  // public-API fixture injected before React mounts. This tests rendering and
  // branch/PR/workflow mapping, not live GitHub network availability.
  await waitForExpression(
    "(() => { const panel = [...document.querySelectorAll('section')].find(node => node.getAttribute('aria-label') === 'Development Monitor'); return !!panel && [...panel.querySelectorAll('a')].some(node => (node.href || '').endsWith('/pull/1')) && panel.querySelectorAll('.development-run-card').length >= 2; })()",
    "the read-only GitHub Development Monitor and PR/workflow telemetry",
    45_000
  );
  const developmentSnapshot = await evaluate(
    "(() => {" +
      "const panel = [...document.querySelectorAll('section')].find(node => node.getAttribute('aria-label') === 'Development Monitor');" +
      "if (!panel) return { found: false };" +
      "const text = panel.innerText || '';" +
      "const shaLink = [...panel.querySelectorAll('a')].find(node => (node.href || '').includes('/commit/'));" +
      "const workflowLinks = [...panel.querySelectorAll('a')].filter(node => (node.href || '').includes('/actions/runs/'));" +
      "return {" +
        "found: true," +
        "hasPr: [...panel.querySelectorAll('a')].some(node => (node.href || '').endsWith('/pull/1'))," +
        "hasBranch: text.includes('feature/four-round-mdt-and-performance')," +
        "headSha: shaLink?.textContent?.trim() || ''," +
        "workflowCards: panel.querySelectorAll('.development-run-card').length - (shaLink ? 1 : 0)," +
        "workflowLinks: workflowLinks.length," +
        "hasUnavailableError: !!panel.querySelector('[role=alert]')" +
      "};" +
    "})()"
  );
  if (
    !developmentSnapshot.found ||
    !developmentSnapshot.hasPr ||
    !developmentSnapshot.hasBranch ||
    !/^[0-9a-f]{12}$/i.test(developmentSnapshot.headSha) ||
    developmentSnapshot.workflowCards !== 2 ||
    developmentSnapshot.workflowLinks !== 2 ||
    developmentSnapshot.hasUnavailableError
  ) {
    throw new Error("Development Monitor did not render verified GitHub branch/PR/workflow metadata: " + JSON.stringify(developmentSnapshot));
  }
  const initialMonitorState = await evaluate(
    "(() => {" +
      "const panel = [...document.querySelectorAll('section')].find(node => node.getAttribute('aria-label') === 'Development Monitor');" +
      "const rows = [...(panel?.querySelectorAll('.mission-run-list .development-run-card') || [])].map(node => node.innerText || '');" +
      "return { currentHeadCount: (panel?.innerText || '').includes('1 / 2'), newestBackend: rows.some(row => row.includes('Run #1188')), staleBackendExcluded: !rows.some(row => row.includes('Run #1187')), hasEarlierCommit: rows.some(row => row.includes('Earlier commit')), hasCurrentCommit: rows.some(row => row.includes('Current branch HEAD')) };" +
    "})()"
  );
  if (
    !initialMonitorState.currentHeadCount ||
    !initialMonitorState.newestBackend ||
    !initialMonitorState.staleBackendExcluded ||
    !initialMonitorState.hasEarlierCommit ||
    !initialMonitorState.hasCurrentCommit
  ) {
    throw new Error("Development Monitor selected stale or misclassified workflow metadata: " + JSON.stringify(initialMonitorState));
  }

  await evaluate("window.__RADONC_DEVELOPMENT_MONITOR_FIXTURE__.mode = 'rate-limit'; true");
  await clickDevelopmentMonitorRefresh();
  await waitForExpression(
    "(() => { const panel = [...document.querySelectorAll('section')].find(node => node.getAttribute('aria-label') === 'Development Monitor'); return !!panel?.querySelector('[role=alert]') && (panel.innerText || '').includes('Showing the last retrieved snapshot.'); })()",
    "the rate-limit warning while retaining the last good Development Monitor snapshot"
  );
  const retainedAfterRateLimit = await evaluate(
    "(() => { const panel = [...document.querySelectorAll('section')].find(node => node.getAttribute('aria-label') === 'Development Monitor'); return { sha: [...panel.querySelectorAll('a')].find(node => (node.href || '').includes('/commit/'))?.textContent?.trim() || '', cards: panel.querySelectorAll('.mission-run-list .development-run-card').length, hasNewestBackend: (panel.innerText || '').includes('Run #1188') }; })()"
  );
  if (retainedAfterRateLimit.sha !== "a1a1a1a1a1a1" || retainedAfterRateLimit.cards !== 2 || !retainedAfterRateLimit.hasNewestBackend) {
    throw new Error("Development Monitor discarded its last good snapshot after HTTP 429: " + JSON.stringify(retainedAfterRateLimit));
  }

  await evaluate("window.__RADONC_DEVELOPMENT_MONITOR_FIXTURE__.mode = 'forbidden'; true");
  await clickDevelopmentMonitorRefresh();
  await waitForExpression(
    "(() => { const panel = [...document.querySelectorAll('section')].find(node => node.getAttribute('aria-label') === 'Development Monitor'); return !!panel?.querySelector('[role=alert]') && (panel.innerText || '').includes('Showing the last retrieved snapshot.'); })()",
    "the HTTP 403 warning while retaining the last good Development Monitor snapshot"
  );

  await evaluate("window.__RADONC_DEVELOPMENT_MONITOR_FIXTURE__.mode = 'incomplete'; true");
  await clickDevelopmentMonitorRefresh();
  await waitForExpression(
    "(() => { const panel = [...document.querySelectorAll('section')].find(node => node.getAttribute('aria-label') === 'Development Monitor'); return (panel?.querySelector('[role=alert]')?.innerText || '').includes('incomplete or inconsistent workflow metadata') && (panel.innerText || '').includes('Showing the last retrieved snapshot.'); })()",
    "inconsistent GitHub workflow metadata to be rejected without replacing the prior snapshot"
  );

  await evaluate("window.__RADONC_DEVELOPMENT_MONITOR_FIXTURE__.mode = 'unusable'; true");
  await clickDevelopmentMonitorRefresh();
  await waitForExpression(
    "(() => { const panel = [...document.querySelectorAll('section')].find(node => node.getAttribute('aria-label') === 'Development Monitor'); return (panel?.querySelector('[role=alert]')?.innerText || '').includes('no usable workflow records') && (panel.innerText || '').includes('Showing the last retrieved snapshot.'); })()",
    "malformed workflow records to be rejected without replacing the prior snapshot"
  );

  await evaluate("window.__RADONC_DEVELOPMENT_MONITOR_FIXTURE__.mode = 'success'; true");
  await clickDevelopmentMonitorRefresh();
  await waitForExpression(
    "(() => { const panel = [...document.querySelectorAll('section')].find(node => node.getAttribute('aria-label') === 'Development Monitor'); return !panel?.querySelector('[role=alert]') && (panel.innerText || '').includes('Run #1188'); })()",
    "Development Monitor recovery after GitHub API errors"
  );

  await evaluate("window.__RADONC_DEVELOPMENT_MONITOR_FIXTURE__.mode = 'empty'; true");
  await clickDevelopmentMonitorRefresh();
  await waitForExpression(
    "(() => { const panel = [...document.querySelectorAll('section')].find(node => node.getAttribute('aria-label') === 'Development Monitor'); return !panel?.querySelector('[role=alert]') && (panel.innerText || '').includes('No workflow runs were returned for this branch.'); })()",
    "a valid API response with zero workflow runs to render as an explicit empty state"
  );
  console.log("DEVELOPMENT_MONITOR_BROWSER_E2E_OK");
  console.log("Verified in headless Edge: newest-run-per-workflow selection, current-HEAD matching, HTTP 403/429 handling, last-good snapshot retention, incomplete/malformed metadata rejection, recovery after errors and a legitimate empty-state response.");

  await waitForExpression(
    "document.body.innerText.includes('Four-round MDT workflow')",
    "the four-round workflow panel"
  );
  await waitForExpression(
    "document.querySelectorAll('.round-stage').length === 3 && " +
      "document.querySelectorAll('.round-agent-list details').length === 90",
    "all three saved round panels and all 90 R2/R3 role records"
  );
  await waitForExpression(
    "!!document.querySelector('.final-mdt-report') && " +
      "document.body.innerText.includes('MDT Chair Synthesis: Dashboard rendering check')",
    "the persisted Chair report"
  );

  await evaluate(
    "(() => { const stages = [...document.querySelectorAll('.round-stage')]; " +
      "for (const index of [1, 2]) { const first = stages[index]?.querySelector('.round-agent-list details'); if (first) first.open = true; } " +
      "return true; })()"
  );
  const rendered = await evaluate(
    "(() => {" +
      "const stages = [...document.querySelectorAll('.round-stage')];" +
      "const headings = stages.map(stage => (stage.querySelector('.round-stage-heading')?.innerText || '').replace(/\\s+/g, ' ').trim());" +
      "const completed = stages.map(stage => (stage.innerText || '').includes('Stage completed'));" +
      "const roundRoleCount = document.querySelectorAll('.round-agent-list details').length;" +
      "const r2First = stages[1]?.querySelector('.round-agent-list details')?.innerText || '';" +
      "const r3First = stages[2]?.querySelector('.round-agent-list details')?.innerText || '';" +
      "const report = document.querySelector('.final-mdt-report')?.innerText || '';" +
      "return { headings, completed, roundRoleCount, " +
        "hasR2SourceReferenceWarning: r2First.includes('Source/provenance integrity flags · review required') && r2First.includes('Peer-scope overclaim'), " +
        "hasServerBoundR2Opinion: r2First.includes('Attributed case-summary opinion responses · source-bound') && r2First.includes('CASE:case_summary#1') && r2First.includes('complete local staging'), " +
        "hasR3SourceOpinionReview: r3First.includes('R3 source-opinion reviews · representation status only') && r3First.includes('Option A') && r3First.includes('conditions: preserved'), " +
        "hasInsufficientInformation: report.includes('Consensus status · insufficient information'), " +
        "hasRecordedAgreementLabel: report.includes('Recorded agreements · attributed, not consensus'), " +
        "hasUncertaintySection: report.includes('Major uncertainties'), " +
        "hasEvidenceLimitation: report.includes('Evidence retrieval is not connected') };" +
    "})()"
  );
  if (
    rendered.headings.length !== 3 ||
    !rendered.completed.every(Boolean) ||
    rendered.roundRoleCount !== 90 ||
    !rendered.hasR2SourceReferenceWarning ||
    !rendered.hasServerBoundR2Opinion ||
    !rendered.hasR3SourceOpinionReview ||
    !rendered.hasInsufficientInformation ||
    !rendered.hasRecordedAgreementLabel ||
    !rendered.hasUncertaintySection ||
    !rendered.hasEvidenceLimitation
  ) {
    throw new Error("The four-round dashboard did not render every saved state and Chair report section: " + JSON.stringify(rendered));
  }

  // The browser fixture is disposable; remove both the test patient and its entire run.
  const deleted = await fetch(API_URL + "/api/patients/" + dashboardPatientId, { method: "DELETE" });
  if (!deleted.ok) {
    throw new Error("The disposable four-round dashboard fixture could not be deleted.");
  }
  dashboardPatientId = null;
  dashboardRunId = null;
  await evaluate("window.localStorage.removeItem('radonc-mdt-active-batch'); true");
  console.log("FOUR_ROUND_DASHBOARD_BROWSER_E2E_OK");
  console.log("Verified in headless Edge: saved R1 readiness, R2/R3 45-role result lists, completed R4 and persisted Chair report rendering. No model inference was invoked.");
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
    // The isolated browser is force-closed during successful cleanup on Windows.
    // Do not report that expected taskkill exit as a failed browser test.
    if (!browserWorkflowCompleted && code !== null && code !== 0) {
      console.error("Edge exited unexpectedly with code " + code);
    }
  });

  const port = await waitForDevToolsPort();
  await connectToPage(port);

  // Give the Development Monitor stable public GitHub API fixtures before
  // React mounts. The production UI still uses the live read-only GitHub API;
  // this browser regression tests its rendering without relying on outbound
  // network access or shared unauthenticated API rate limits.
  const githubApiFixture = String.raw`(() => {
    const realFetch = window.fetch.bind(window);
    const apiBase = "https://api.github.com/repos/drvishnua/RadOnc-MDT-Simulator";
    const branch = "feature/four-round-mdt-and-performance";
    const headSha = "a1".repeat(20);
    const checkedAt = "2026-11-17T01:44:00Z";
    const pullRequest = {
      number: 1,
      state: "open",
      draft: true,
      html_url: "https://github.com/drvishnua/RadOnc-MDT-Simulator/pull/1",
      updated_at: checkedAt,
      head: { ref: branch, sha: headSha },
      base: { ref: "main" }
    };
    const runs = {
      total_count: 3,
      workflow_runs: [
        {
          id: 7100001, workflow_id: 101, name: "Backend Tests", run_number: 1188,
          status: "completed", conclusion: "success", event: "pull_request",
          head_sha: headSha, created_at: "2026-11-17T01:43:00Z",
          updated_at: checkedAt,
          html_url: "https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/7100001"
        },
        {
          id: 7100003, workflow_id: 101, name: "Backend Tests", run_number: 1187,
          status: "completed", conclusion: "success", event: "pull_request",
          head_sha: headSha, created_at: "2026-11-17T01:41:00Z",
          updated_at: "2026-11-17T01:41:00Z",
          html_url: "https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/7100003"
        },
        {
          id: 7100002, workflow_id: 102,
          name: "Patient Registry and Four-Round Dashboard Browser E2E", run_number: 400,
          status: "completed", conclusion: "success", event: "pull_request",
          head_sha: "b2".repeat(20), created_at: "2026-11-17T01:42:00Z",
          updated_at: checkedAt,
          html_url: "https://github.com/drvishnua/RadOnc-MDT-Simulator/actions/runs/7100002"
        }
      ]
    };
    window.__RADONC_DEVELOPMENT_MONITOR_FIXTURE__ = { mode: "success" };
    const jsonResponse = (payload, status = 200) => new Response(JSON.stringify(payload), {
      status,
      headers: { "Content-Type": "application/json" }
    });
    window.fetch = (input, init) => {
      const url = typeof input === "string" ? input : (input && input.url) || String(input);
      const mode = window.__RADONC_DEVELOPMENT_MONITOR_FIXTURE__.mode;
      if (url === apiBase + "/pulls/1") return Promise.resolve(jsonResponse(pullRequest));
      if (url.startsWith(apiBase + "/actions/runs?")) {
        if (mode === "rate-limit") return Promise.resolve(jsonResponse({ message: "API rate limit exceeded" }, 429));
        if (mode === "forbidden") return Promise.resolve(jsonResponse({ message: "API access restricted" }, 403));
        if (mode === "incomplete") return Promise.resolve(jsonResponse({ total_count: 2, workflow_runs: [] }));
        if (mode === "unusable") return Promise.resolve(jsonResponse({
          total_count: 1,
          workflow_runs: [{ id: 7100004, created_at: checkedAt }]
        }));
        if (mode === "empty") return Promise.resolve(jsonResponse({ total_count: 0, workflow_runs: [] }));
        return Promise.resolve(jsonResponse(runs));
      }
      return realFetch(input, init);
    };
  })();`;
  await sendCommand("Page.addScriptToEvaluateOnNewDocument", { source: githubApiFixture });
  await sendCommand("Page.reload", { ignoreCache: true });

  await waitForExpression("!!document.querySelector('.app-shell')", "React application mount");
  await waitForExpression(
    "(() => { const label = [...document.querySelectorAll('label')].find(node => (node.innerText || '').trim().startsWith('Registered patient')); return !!label && !!label.querySelector('select'); })()",
    "the patient registry selector"
  );

  await setLabelValue("Fictional patient name", originalName);
  await setLabelValue("Diagnosis / MDT case title", originalTitle);
  await setLabelValue("Clinical summary", originalSummary);
  await setAllStructuredFieldValues();
  await waitForValidationReady();
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
  await assertAllStructuredFieldValues();

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
  await assertAllStructuredFieldValues();

  // Change one field only; every other narrative and structured field must remain intact.
  await setLabelValue("Clinical summary", updatedSummary);
  await waitForValidationReady();
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
  await assertFieldValue("Fictional patient name", originalName);
  await assertFieldValue("Clinical summary", updatedSummary);
  await assertAllStructuredFieldValues();

  await selectOptionByText("Saved case version", "Version 1 ·");
  await clickButton("Load version");
  await waitForExpression(
    "(() => { const button = [...document.querySelectorAll('button')].find(node => (node.innerText || '').trim().startsWith('Delete patient and linked results')); return !!button && !button.disabled; })()",
    "the restored patient action controls to finish rendering before deletion"
  );
  await assertFieldValue("Fictional patient name", originalName);
  await assertFieldValue("Clinical summary", originalSummary);
  await assertAllStructuredFieldValues();
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
  console.log("Verified in headless Edge: all case fields round-trip through create/reload; one-field edit; immutable version 2; restore version 1; delete.");
  console.log("Disposable registry identifier: " + patientIdentifier);

  await verifyFourRoundDashboard();
  browserWorkflowCompleted = true;
} finally {
  if (dashboardPatientId) {
    await fetch(API_URL + "/api/patients/" + dashboardPatientId, { method: "DELETE" })
      .catch(error => console.error("Dashboard fixture cleanup warning: " + error.message));
  }
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
