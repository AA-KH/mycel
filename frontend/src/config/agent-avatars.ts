/**
 * Pixel-art portrait assignments for every Mycel agent.
 * Portraits live in /public/avatars/ — each team gets a unique set
 * so no two members of the same team share a face.
 */

export const AGENT_AVATARS: Record<string, string> = {
  // Creative
  emp_cre_creator_001: "/avatars/m1.png", // Vihaan Kapoor
  emp_cre_director_001: "/avatars/f1.png", // Riya Sharma
  emp_cre_editor_001: "/avatars/m2.png", // Arjun Malhotra
  emp_cre_motion_001: "/avatars/f2.png", // Kavya Mehta
  // Developer
  emp_dev_frontend_001: "/avatars/f3.png", // Ananya Mehta
  emp_dev_backend_001: "/avatars/m3.png", // Kabir Sharma
  emp_dev_devops_001: "/avatars/f4.png", // Ishita Kapoor
  emp_dev_qa_001: "/avatars/m4.png", // Rohan Verma
  // Finance
  emp_fin_accounting_001: "/avatars/m5.png", // Rahul Mehta
  emp_fin_analyst_001: "/avatars/f5.png", // Priya Sharma
  emp_fin_budget_001: "/avatars/f6.png", // Sneha Kapoor
  // Legal
  emp_leg_analyst_001: "/avatars/m6.png", // Raghav Mehta
  emp_leg_contract_001: "/avatars/f7.png", // Isha Verma
  emp_leg_researcher_001: "/avatars/f1.png", // Aditi Sharma
  emp_leg_reviewer_001: "/avatars/m7.png", // Armaan Kapoor
  // Marketing
  emp_mkt_analyst_001: "/avatars/m1.png", // Dev Malhotra
  emp_mkt_content_001: "/avatars/m2.png", // Karan Mehta
  emp_mkt_growth_001: "/avatars/f2.png", // Simran Kapoor
  emp_mkt_strategist_001: "/avatars/f3.png", // Neha Sharma
  // Operations
  emp_ops_analyst_001: "/avatars/f4.png", // Kriti Mehta
  emp_ops_coordinator_001: "/avatars/m3.png", // Rohit Sharma
  emp_ops_manager_001: "/avatars/f5.png", // Ananya Verma
  emp_ops_specialist_001: "/avatars/m4.png", // Samar Kapoor
  // Research
  emp_res_analyst_001: "/avatars/f6.png", // Meera Sharma
  emp_res_factchecker_001: "/avatars/m5.png", // Aditya Rao
  emp_res_researcher_001: "/avatars/m6.png", // Aarav Mehta
  emp_res_writer_001: "/avatars/f7.png", // Nisha Kapoor
};

export function getAgentAvatar(memberId: string): string {
  return AGENT_AVATARS[memberId] ?? "/avatars/m1.png";
}
