export interface LandmarkTrial {
  id: string;
  name: string;
  citation: string;
  phase: string;
  year: number;
  primarySite: string;
  population: string;
  primaryEndpoint: string;
  outcome: string;
  radOncTakeaway: string;
  pmid: string;
  guidelineLevel: string;
}

export const LANDMARK_TRIALS: LandmarkTrial[];

export interface OrganConstraint {
  id: string;
  anatomicalSite: string;
  organ: string;
  metric: string;
  limitValue: number;
  unit: string;
  operator: string;
  endpoint: string;
  riskLevel: "standard_safe" | "acceptable_risk" | "high_risk";
  fractionationType: string;
}

export function getSiteConstraints(site: string): OrganConstraint[];

export function findTrialByKeyword(query: string): LandmarkTrial | undefined;
