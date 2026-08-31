import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from teams.validation.models import TeamReadiness
from teams.registry import TeamRegistry, TeamCatalogue
from execution.pipelines.registry import PipelineRegistry
from teams.resolver import TeamCapabilityResolver
from teams.validator import TeamValidator
from teams.seed import seed

def main():
    print("Initializing Registries...")
    tr = TeamRegistry()
    pr = PipelineRegistry(tr)
    
    # Load all seeds into registries
    print("Loading Team Catalogue...")
    seed_data = seed()
    for team in seed_data["teams"]:
        try:
            tr.register(team)
        except: pass
    for pipe in seed_data["pipelines"]:
        try:
            pr.register(pipe)
        except: pass
        
    resolver = TeamCapabilityResolver(tr, pr)
    validator = TeamValidator(tr, pr, resolver)
    
    print("Validating Teams...")
    summary = validator.validate_all()
    
    print("\n============================================")
    print("Mycel Team Validation Report")
    print("============================================")
    print(f"Teams checked: {summary.total_teams}")
    print(f"Ready: {summary.ready_teams}")
    print(f"Warnings: {summary.warnings}")
    print(f"Errors: {summary.errors}\n")
    
    for res in summary.results:
        print(f"{res.team_id.capitalize()}: {res.readiness.value}")
        if res.errors:
            for err in res.errors:
                print(f"  [ERROR] {err.code}: {err.message}")
        if res.warnings:
            for warn in res.warnings:
                print(f"  [WARN] {warn.code}: {warn.message}")
                
    if summary.errors > 0:
        sys.exit(1)

if __name__ == "__main__":
    main()
