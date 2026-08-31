export type AgentStatus = "working" | "complete" | "walking" | "on_break" | "failure";

export type BreakActivity = "chai" | "scrolling_reels" | "smoke_break" | "chatting";

export type AgentRole =
  | "Frontend Developer"
  | "Backend Developer"
  | "QA Engineer"
  | "Code Reviewer"
  | "DevOps Engineer"
  | "Technical Writer"
  | "Debugger"
  | "Architect"
  | "Designer"
  | "Data Engineer"
  | "Developer"
  // Company-level roles
  | "Orchestrator"
  | "HR Agent";

export interface AgentSession {
  id: string;
  session_id: string;
  role: AgentRole;
  status: AgentStatus;
  break_activity: BreakActivity | null;
  team: string;
  employee_name: string | null;
  summary: string | null;
  link: string | null;
  workspace: string | null;
  started_at: string;
  last_heartbeat_at: string;
  current_task_id: string | null;
}

export interface ApiKeyItem {
  id: string;
  key_prefix: string;
  name: string;
  created_at: string;
  last_used_at: string | null;
  is_active: boolean;
}

export interface DeskPosition {
  x: number;
  y: number;
  direction: "left" | "right";
  zone: string;
}

export interface OfficeScene {
  level: number;
  name: string;
  nameZh: string;
  minAgents: number;
  maxAgents: number;
  description: string;
  bgColor: string;
  floorColor: string;
  wallColor: string;
  accentColor: string;
  deskPositions: DeskPosition[];
  decorations: string[];
}

export type SeatZone = "work" | "break" | "meeting" | "idle";

export interface SeatPosition {
  x: number;
  y: number;
  direction: "up" | "down" | "left" | "right";
  deskX: number;
  deskY: number;
  zone: SeatZone;
}

export interface TileLayer {
  name: string;
  data: number[];
  depth: number;
}

export interface TileMapData {
  width: number;
  height: number;
  tileSize: number;
  layers: TileLayer[];
  seats: SeatPosition[];
}

// ── Wallet Card (HR Assignment Flow) ────────────────────────────

export type WalletCardStatus = "assigned" | "in_progress" | "done";

export interface WalletCard {
  id: string;
  task_id: string;
  agent_id: string;
  agent_role: AgentRole;
  agent_name: string;
  task_title: string;
  team: string;
  issued_by: "hr_agent";
  issued_at: string;
  status: WalletCardStatus;
  completed_summary: string | null;
}

// ── Orchestration Pipeline (Real-time Visualization) ────────────

export const OrchestrationPhase = {
  TASK_RECEIVED: "TASK_RECEIVED",
  HR_ANALYSIS_STARTED: "HR_ANALYSIS_STARTED",
  CAPABILITY_IDENTIFIED: "CAPABILITY_IDENTIFIED",
  TEAM_SELECTION_STARTED: "TEAM_SELECTION_STARTED",
  TEAM_SELECTED: "TEAM_SELECTED",
  MEMBER_SELECTION_STARTED: "MEMBER_SELECTION_STARTED",
  MEMBER_SELECTED: "MEMBER_SELECTED",
  TEAM_ASSEMBLED: "TEAM_ASSEMBLED",
  WORKFORCE_ASSEMBLED: "WORKFORCE_ASSEMBLED",
  TASK_ASSIGNED: "TASK_ASSIGNED",
  AGENT_MOVING: "AGENT_MOVING",
  EXECUTION_STARTED: "EXECUTION_STARTED",
  AGENT_WORKING: "AGENT_WORKING",
  AGENT_COMPLETED: "AGENT_COMPLETED",
  AGENT_FAILED: "AGENT_FAILED",
  ORCHESTRATION_COMPLETED: "ORCHESTRATION_COMPLETED",
  ORCHESTRATION_FAILED: "ORCHESTRATION_FAILED",
} as const;
export type OrchestrationPhase = (typeof OrchestrationPhase)[keyof typeof OrchestrationPhase];

/** Human-readable labels for each orchestration phase */
export const ORCHESTRATION_PHASE_LABELS: Record<OrchestrationPhase, string> = {
  [OrchestrationPhase.TASK_RECEIVED]: "Task Received",
  [OrchestrationPhase.HR_ANALYSIS_STARTED]: "HR Analysis Started",
  [OrchestrationPhase.CAPABILITY_IDENTIFIED]: "Capability Identified",
  [OrchestrationPhase.TEAM_SELECTION_STARTED]: "Team Selection Started",
  [OrchestrationPhase.TEAM_SELECTED]: "Team Selected",
  [OrchestrationPhase.MEMBER_SELECTION_STARTED]: "Member Selection Started",
  [OrchestrationPhase.MEMBER_SELECTED]: "Member Selected",
  [OrchestrationPhase.TEAM_ASSEMBLED]: "Team Assembled",
  [OrchestrationPhase.WORKFORCE_ASSEMBLED]: "Workforce Assembled",
  [OrchestrationPhase.TASK_ASSIGNED]: "Task Assigned",
  [OrchestrationPhase.AGENT_MOVING]: "Agent Moving",
  [OrchestrationPhase.EXECUTION_STARTED]: "Execution Started",
  [OrchestrationPhase.AGENT_WORKING]: "Agent Working",
  [OrchestrationPhase.AGENT_COMPLETED]: "Agent Completed",
  [OrchestrationPhase.AGENT_FAILED]: "Agent Failed",
  [OrchestrationPhase.ORCHESTRATION_COMPLETED]: "Orchestration Completed",
  [OrchestrationPhase.ORCHESTRATION_FAILED]: "Orchestration Failed",
};

/** Color for each orchestration phase step indicator */
export const ORCHESTRATION_PHASE_COLORS: Record<OrchestrationPhase, string> = {
  [OrchestrationPhase.TASK_RECEIVED]: "#6aa9ff",
  [OrchestrationPhase.HR_ANALYSIS_STARTED]: "#4ecdc4",
  [OrchestrationPhase.CAPABILITY_IDENTIFIED]: "#f2b01f",
  [OrchestrationPhase.TEAM_SELECTION_STARTED]: "#b197fc",
  [OrchestrationPhase.TEAM_SELECTED]: "#b197fc",
  [OrchestrationPhase.MEMBER_SELECTION_STARTED]: "#ffa07a",
  [OrchestrationPhase.MEMBER_SELECTED]: "#ffa07a",
  [OrchestrationPhase.TEAM_ASSEMBLED]: "#79d97c",
  [OrchestrationPhase.WORKFORCE_ASSEMBLED]: "#79d97c",
  [OrchestrationPhase.TASK_ASSIGNED]: "#ffa07a",
  [OrchestrationPhase.AGENT_MOVING]: "#4ecdc4",
  [OrchestrationPhase.EXECUTION_STARTED]: "#ffd93d",
  [OrchestrationPhase.AGENT_WORKING]: "#ffd93d",
  [OrchestrationPhase.AGENT_COMPLETED]: "#79d97c",
  [OrchestrationPhase.AGENT_FAILED]: "#e5484d",
  [OrchestrationPhase.ORCHESTRATION_COMPLETED]: "#79d97c",
  [OrchestrationPhase.ORCHESTRATION_FAILED]: "#e5484d",
};

export type OrchestrationStepStatus = "pending" | "active" | "complete" | "failed";

export interface OrchestrationPayload {
  detail?: string;
  team_id?: string;
  team_name?: string;
  employee_id?: string;
  employee_name?: string;
  employee_role?: string;
  session_id?: string;
  wallet_card_id?: string;
  subtask_id?: string;
  match_score?: number;
  capabilities?: string[];
  selected_teams?: string[];
  metadata?: Record<string, any>;
  subtask_index?: number;
  total_subtasks?: number;
}

export interface OrchestrationEvent {
  event_id: string;
  task_id: string;
  event_type: string;
  phase: OrchestrationPhase;
  phase_index?: number;
  timestamp: string;
  actor: string;
  payload: OrchestrationPayload;
}

export interface OrchestrationStep extends OrchestrationEvent {
  status: OrchestrationStepStatus;
}

export interface OrchestrationEmployee {
  employee_id: string;
  employee_name: string;
  employee_role: string;
  team_name: string;
  session_id?: string;
  wallet_card_id?: string;
  subtask_id?: string;
  subtask_description?: string;
  match_score?: number;
  capabilities?: string[];
  status: "hired" | "assigned" | "moving" | "working" | "completed" | "failed";
}

export interface OrchestrationState {
  task_id: string | null;
  current_phase: OrchestrationPhase | null;
  steps: OrchestrationStep[];
  selected_teams: string[];
  selected_employees: Record<string, OrchestrationEmployee>;
  is_active: boolean;
  is_workforce_assembled: boolean;
  started_at: string | null;
  completed_at: string | null;
}
