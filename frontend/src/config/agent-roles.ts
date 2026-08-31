import type { AgentStatus } from "../types/agent";

export const ROLE_CONFIGS: Record<string, { color: string; emoji: string; label: string }> = {
  "Frontend Developer": { color: "#61dafb", emoji: "⚛️", label: "Frontend" },
  "Backend Developer": { color: "#68a063", emoji: "🐍", label: "Backend" },
  "QA Engineer": { color: "#ff5722", emoji: "🐛", label: "QA" },
  "Code Reviewer": { color: "#9c27b0", emoji: "👀", label: "Reviewer" },
  "DevOps Engineer": { color: "#2196f3", emoji: "🚀", label: "DevOps" },
  "Technical Writer": { color: "#ff9800", emoji: "📝", label: "Researcher" },
  "Debugger": { color: "#e91e63", emoji: "🔧", label: "Debugger" },
  "Architect": { color: "#3f51b5", emoji: "🏗️", label: "Manager" },
  "Designer": { color: "#e91e63", emoji: "🎨", label: "Designer" },
  "Data Engineer": { color: "#4caf50", emoji: "📊", label: "Data" },
  "Developer": { color: "#607d8b", emoji: "💻", label: "Coder" },
  // Company-level agents
  "Orchestrator": { color: "#a78bfa", emoji: "👔", label: "Orchestrator" },
  "HR Agent": { color: "#f472b6", emoji: "🤝", label: "HR Agent" },
  // Mycel native agent roles
  "manager": { color: "#a78bfa", emoji: "👔", label: "Manager" },
  "coder": { color: "#34d399", emoji: "💻", label: "Coder" },
  "researcher": { color: "#60a5fa", emoji: "🔍", label: "Researcher" },
  "reviewer": { color: "#f472b6", emoji: "👁️", label: "Reviewer" },
  "tester": { color: "#fb923c", emoji: "🧪", label: "Tester" },
  // company-in-a-box roles
  "client-manager": { color: "#34d399", emoji: "🤝", label: "Client Manager" },
  "scope-change-handler": { color: "#c084fc", emoji: "👔", label: "Scope Change Handler" },
  "design-system-manager": { color: "#fbbf24", emoji: "🎨", label: "Design System Manager" },
  "ui-designer": { color: "#2dd4bf", emoji: "🎨", label: "Ui Designer" },
  "ux-researcher": { color: "#38bdf8", emoji: "🔍", label: "Ux Researcher" },
  "backend-architect": { color: "#f472b6", emoji: "⚙️", label: "Backend Architect" },
  "code-reviewer": { color: "#818cf8", emoji: "👀", label: "Code Reviewer" },
  "estimator": { color: "#818cf8", emoji: "⏱️", label: "Estimator" },
  "frontend-developer": { color: "#f87171", emoji: "💻", label: "Frontend Developer" },
  "infrastructure-maintainer": { color: "#2dd4bf", emoji: "🏗️", label: "Infrastructure Maintainer" },
  "contract-reviewer": { color: "#a78bfa", emoji: "📄", label: "Contract Reviewer" },
  "ip-protector": { color: "#c084fc", emoji: "🔒", label: "Ip Protector" },
  "nda-manager": { color: "#a3e635", emoji: "🤫", label: "Nda Manager" },
  "analytics-reporter": { color: "#2dd4bf", emoji: "📈", label: "Analytics Reporter" },
  "content-creator": { color: "#f87171", emoji: "✍️", label: "Content Creator" },
  "distribution-manager": { color: "#a3e635", emoji: "🚀", label: "Distribution Manager" },
  "experiment-tracker": { color: "#38bdf8", emoji: "🧪", label: "Experiment Tracker" },
  "launch-strategist": { color: "#60a5fa", emoji: "🎉", label: "Launch Strategist" },
  "test-results-analyzer": { color: "#4ade80", emoji: "🔬", label: "Test Results Analyzer" },
  "tiktok-strategist": { color: "#34d399", emoji: "📱", label: "Tiktok Strategist" },
  "finance-tracker": { color: "#fbbf24", emoji: "💰", label: "Finance Tracker" },
  "knowledge-manager": { color: "#c084fc", emoji: "📚", label: "Knowledge Manager" },
  "onboarding-coordinator": { color: "#e879f9", emoji: "👋", label: "Onboarding Coordinator" },
  "support-responder": { color: "#34d399", emoji: "🎧", label: "Support Responder" },
  "vision-keeper": { color: "#a78bfa", emoji: "🔭", label: "Vision Keeper" },
  "feedback-synthesizer": { color: "#4ade80", emoji: "💬", label: "Feedback Synthesizer" },
  "opportunity-evaluator": { color: "#4ade80", emoji: "💡", label: "Opportunity Evaluator" },
  "product-manager": { color: "#f87171", emoji: "📦", label: "Product Manager" },
  "sprint-planner": { color: "#fb7185", emoji: "🏃", label: "Sprint Planner" },
  "delivery-manager": { color: "#818cf8", emoji: "🚚", label: "Delivery Manager" },
  "priority-arbiter": { color: "#60a5fa", emoji: "⚖️", label: "Priority Arbiter" },
  "release-retrospective-owner": { color: "#f87171", emoji: "🔄", label: "Release Retrospective Owner" },
  "account-executive": { color: "#fbbf24", emoji: "💼", label: "Account Executive" },
  "proposal-writer": { color: "#4ade80", emoji: "📝", label: "Proposal Writer" },
  "sales-developer": { color: "#fbbf24", emoji: "💰", label: "Sales Developer" },
  "access-controller": { color: "#60a5fa", emoji: "🔑", label: "Access Controller" },
  "compliance-monitor": { color: "#e879f9", emoji: "🛡️", label: "Compliance Monitor" },
  "incident-responder": { color: "#818cf8", emoji: "🚨", label: "Incident Responder" },
  "security-auditor": { color: "#f472b6", emoji: "🔐", label: "Security Auditor" },
  "automation-engineer": { color: "#fb7185", emoji: "🤖", label: "Automation Engineer" },
  "bug-triager": { color: "#a3e635", emoji: "🐛", label: "Bug Triager" },
  "qa-tester": { color: "#a3e635", emoji: "🔬", label: "Qa Tester" },
};

export const STATUS_COLORS: Record<AgentStatus, { bg: string; label: string }> = {
  working: { bg: "#a3be8c", label: "Working" },
  complete: { bg: "#88c0d0", label: "Complete" },
  walking: { bg: "#ebcb8b", label: "Walking" },
  on_break: { bg: "#d08770", label: "On Break" },
  failure: { bg: "#bf616a", label: "Failed" },
};

// ── Team Registry (sourced from backend/teams/) ─────────────────────────────

export interface TeamMember {
  id: string;
  name: string;
  title: string;
}

export interface TeamInfo {
  label: string;
  color: string;
  emoji: string;
  floorColor: string;
  members: TeamMember[];
}

export const TEAM_REGISTRY: Record<string, TeamInfo> = {
  creative: {
    label: "Creative",
    color: "#c084fc",
    emoji: "🎨",
    floorColor: "#7c3aed",
    members: [
      { id: "emp_cre_creator_001", name: "Vihaan Kapoor", title: "Content Creator" },
      { id: "emp_cre_director_001", name: "Riya Sharma", title: "Creative Director" },
      { id: "emp_cre_editor_001", name: "Arjun Malhotra", title: "Video Editor" },
      { id: "emp_cre_motion_001", name: "Kavya Mehta", title: "Motion Designer" },
    ],
  },
  developer: {
    label: "Developer",
    color: "#34d399",
    emoji: "💻",
    floorColor: "#059669",
    members: [
      { id: "emp_dev_frontend_001", name: "Ananya Mehta", title: "Frontend Engineer" },
      { id: "emp_dev_backend_001", name: "Kabir Sharma", title: "Backend Engineer" },
      { id: "emp_dev_devops_001", name: "Ishita Kapoor", title: "DevOps Engineer" },
      { id: "emp_dev_qa_001", name: "Rohan Verma", title: "QA Engineer" },
    ],
  },
  finance: {
    label: "Finance",
    color: "#fbbf24",
    emoji: "💰",
    floorColor: "#d97706",
    members: [
      { id: "emp_fin_accounting_001", name: "Rahul Mehta", title: "Accounts Specialist" },
      { id: "emp_fin_analyst_001", name: "Priya Sharma", title: "Finance Analyst" },
      { id: "emp_fin_budget_001", name: "Sneha Kapoor", title: "Budget Planner" },
    ],
  },
  legal: {
    label: "Legal",
    color: "#60a5fa",
    emoji: "⚖️",
    floorColor: "#2563eb",
    members: [
      { id: "emp_leg_analyst_001", name: "Raghav Mehta", title: "Legal Analyst" },
      { id: "emp_leg_contract_001", name: "Isha Verma", title: "Contract Specialist" },
      { id: "emp_leg_researcher_001", name: "Aditi Sharma", title: "Legal Researcher" },
      { id: "emp_leg_reviewer_001", name: "Armaan Kapoor", title: "Legal Reviewer" },
    ],
  },
  marketing: {
    label: "Marketing",
    color: "#f472b6",
    emoji: "📈",
    floorColor: "#db2777",
    members: [
      { id: "emp_mkt_analyst_001", name: "Dev Malhotra", title: "Marketing Analyst" },
      { id: "emp_mkt_content_001", name: "Karan Mehta", title: "Content Creator" },
      { id: "emp_mkt_growth_001", name: "Simran Kapoor", title: "Growth Specialist" },
      { id: "emp_mkt_strategist_001", name: "Neha Sharma", title: "Marketing Strategist" },
    ],
  },
  operations: {
    label: "Operations",
    color: "#fb923c",
    emoji: "⚙️",
    floorColor: "#c2410c",
    members: [
      { id: "emp_ops_analyst_001", name: "Kriti Mehta", title: "Process Analyst" },
      { id: "emp_ops_coordinator_001", name: "Rohit Sharma", title: "Ops Coordinator" },
      { id: "emp_ops_manager_001", name: "Ananya Verma", title: "Ops Manager" },
      { id: "emp_ops_specialist_001", name: "Samar Kapoor", title: "Ops Specialist" },
    ],
  },
  research: {
    label: "Research",
    color: "#2dd4bf",
    emoji: "🔍",
    floorColor: "#0d9488",
    members: [
      { id: "emp_res_analyst_001", name: "Meera Sharma", title: "Research Analyst" },
      { id: "emp_res_factchecker_001", name: "Aditya Rao", title: "Fact Checker" },
      { id: "emp_res_researcher_001", name: "Aarav Mehta", title: "Researcher" },
      { id: "emp_res_writer_001", name: "Nisha Kapoor", title: "Research Writer" },
    ],
  },
};

/** Get all team members as a flat list */
export function getAllMembers(): Array<TeamMember & { team: string }> {
  const members: Array<TeamMember & { team: string }> = [];
  for (const [teamId, team] of Object.entries(TEAM_REGISTRY)) {
    for (const member of team.members) {
      members.push({ ...member, team: teamId });
    }
  }
  return members;
}

/** Get team by member employee ID */
export function getTeamByMemberId(memberId: string): string | null {
  for (const [teamId, team] of Object.entries(TEAM_REGISTRY)) {
    if (team.members.some((m) => m.id === memberId)) {
      return teamId;
    }
  }
  return null;
}
