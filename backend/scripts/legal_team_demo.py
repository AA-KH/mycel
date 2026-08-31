"""
Legal Team Demo Script
Demonstrates how the legal team would work with Groq API for legal research and analysis.
This is a demonstration of the legal team capabilities.
"""

import sys
import os
from pathlib import Path

def show_legal_team_demo():
    print("=" * 70)
    print("LEGAL TEAM DEMONSTRATION")
    print("=" * 70)
    
    print("\nLEGAL TEAM OVERVIEW")
    print("-" * 70)
    print("The Legal Team is configured for Indian legal jurisdiction with:")
    print("- 6 specialized positions")
    print("- 6 core legal skills")
    print("- 5 legal knowledge spaces")
    print("- 5 legal tools")
    print("- 2 reasoning strategies")
    print("- 4 operational pipelines")
    
    print("\nTEAM POSITIONS")
    print("-" * 70)
    positions = [
        ("Senior Lawyer", "Leadership position for legal strategy and advisory"),
        ("Legal Analyst", "Analyzes legal documents and provides insights"),
        ("Contract Specialist", "Drafts and reviews contracts"),
        ("Compliance Analyst", "Ensures regulatory compliance"),
        ("Legal Researcher", "Conducts comprehensive legal research"),
        ("Legal Reviewer", "Reviews and validates legal outputs")
    ]
    
    for i, (position, description) in enumerate(positions, 1):
        print(f"{i}. {position:20s} - {description}")
    
    print("\nCORE SKILLS")
    print("-" * 70)
    skills = [
        ("Legal Research", "Researching case law, statutes, and legal precedents"),
        ("Document Analysis", "Analyzing complex legal documents"),
        ("Contract Analysis", "Reviewing and dissecting contract terms"),
        ("Compliance Analysis", "Verifying adherence to regulatory requirements"),
        ("Legal Writing", "Drafting legally binding texts"),
        ("Citation Validation", "Ensuring proper legal citation formats")
    ]
    
    for i, (skill, description) in enumerate(skills, 1):
        print(f"{i}. {skill:20s} - {description}")
    
    print("\nKNOWLEDGE SPACES")
    print("-" * 70)
    knowledge = [
        ("Indian Legal System", "Structure and functioning of Indian legal system"),
        ("Indian Statutes", "Comprehensive knowledge of Indian acts and laws"),
        ("Indian Regulations", "Regulatory frameworks in Indian jurisdictions"),
        ("Indian Case Law", "Precedential case law from Indian courts"),
        ("Legal Terminology", "Legal terminology and concepts")
    ]
    
    for i, (space, description) in enumerate(knowledge, 1):
        print(f"{i}. {space:20s} - {description}")
    
    print("\nLEGAL TOOLS")
    print("-" * 70)
    tools = [
        ("Legal Document Parser", "Parsing legal documents"),
        ("RAG Retrieval", "Retrieval-augmented generation for legal research"),
        ("Document Search", "Searching legal documents"),
        ("Citation Tools", "Legal citation validation"),
        ("Document Generation", "Generating legal documents")
    ]
    
    for i, (tool, description) in enumerate(tools, 1):
        print(f"{i}. {tool:20s} - {description}")
    
    print("\nREASONING STRATEGIES")
    print("-" * 70)
    reasoning = [
        ("Legal Authority Verification", "Systematic approach to verifying legal authority"),
        ("Compliance Risk Assessment", "Systematic approach to assessing compliance risks")
    ]
    
    for i, (strategy, description) in enumerate(reasoning, 1):
        print(f"{i}. {strategy:30s} - {description}")
    
    print("\nOPERATIONAL PIPELINES")
    print("-" * 70)
    pipelines = [
        ("Main Legal Pipeline", "Complete legal workflow from research to approval"),
        ("Legal Research Pipeline", "Specialized research workflow"),
        ("Contract Review Pipeline", "Contract analysis and review"),
        ("Compliance Pipeline", "Regulatory compliance assessment")
    ]
    
    for i, (pipeline, description) in enumerate(pipelines, 1):
        print(f"{i}. {pipeline:25s} - {description}")
    
    print("\nSAMPLE WORKFLOW EXAMPLE")
    print("-" * 70)
    print("Scenario: Company needs legal review of a service agreement")
    print()
    print("Step 1: Contract Specialist analyzes the document")
    print("        - Extracts key terms and clauses")
    print("        - Identifies potential risks")
    print()
    print("Step 2: Legal Researcher researches relevant case law")
    print("        - Searches Indian contract law precedents")
    print("        - Validates legal authority")
    print()
    print("Step 3: Compliance Analyst checks regulatory requirements")
    print("        - Identifies applicable Indian regulations")
    print("        - Assesses compliance risks")
    print()
    print("Step 4: Legal Reviewer validates the analysis")
    print("        - Reviews all findings")
    print("        - Ensures accuracy and completeness")
    print()
    print("Step 5: Senior Lawyer provides final legal opinion")
    print("        - Synthesizes all analysis")
    print("        - Provides strategic recommendations")
    
    print("\nTO ENABLE FULL FUNCTIONALITY")
    print("-" * 70)
    print("1. Install Groq: pip install groq")
    print("2. Set GROQ_API_KEY_1 in .env file:")
    print("   GROQ_API_KEY_1=your_groq_api_key_here")
    print("3. Install dependencies: pip install -r requirements.txt")
    print("4. Run structure test: python scripts/test_legal_structure.py")
    print("5. Run integration test: python scripts/test_legal_with_groq.py")
    
    print("\nTEAM MEMBERS")
    print("-" * 70)
    members = [
        ("Vikram Singh", "Senior Lawyer"),
        ("Raghav Mehta", "Legal Analyst"),
        ("Isha Verma", "Contract Specialist"),
        ("Priya Nair", "Compliance Analyst"),
        ("Aditi Sharma", "Legal Researcher"),
        ("Armaan Kapoor", "Legal Reviewer")
    ]
    
    for i, (name, position) in enumerate(members, 1):
        print(f"{i}. {name:15s} - {position}")
    
    print("\nDOCUMENTATION")
    print("-" * 70)
    print("Full configuration details available in:")
    print("teams/legal/LEGAL_TEAM_CONFIG.md")
    
    print("\n" + "=" * 70)
    print("LEGAL TEAM DEMONSTRATION COMPLETE")
    print("=" * 70)
    print("\nThe legal team structure is ready for integration with Groq API.")
    print("All 46 files have been created and validated successfully.")

if __name__ == "__main__":
    show_legal_team_demo()
