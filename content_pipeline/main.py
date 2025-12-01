"""
Main Pipeline Orchestrator
Coordinates execution of all pipeline stages
"""
import os
import sys
import uuid
import traceback
from typing import Dict, Any, Optional
from datetime import datetime

from utils import db
from utils.validation import validate_url

# Import stage modules
from stages import stage1_extract
from stages import stage2_analyze
from stages import stage3_safety
from stages import stage4_rag_setup
from stages import stage5_outline
from stages import stage6_generate
from stages import stage7_qa
from stages import stage8_format


def execute_stage(
    pipeline_id: str,
    stage_num: int,
    stage_func,
    *args,
    **kwargs
) -> Dict[str, Any]:
    """
    Execute a pipeline stage with error handling
    
    Args:
        pipeline_id: Pipeline identifier
        stage_num: Stage number
        stage_func: Stage function to execute
        *args: Positional arguments for stage
        **kwargs: Keyword arguments for stage
        
    Returns:
        Stage output dictionary
    """
    try:
        print(f"\n{'='*60}")
        print(f"Executing Stage {stage_num}")
        print(f"{'='*60}")
        
        # Execute stage
        print(f"[DEBUG execute_stage] Calling stage {stage_num} with args: {len(args)} positional, {len(kwargs)} keyword")
        if stage_num == 6 and len(args) > 1:
            # Debug what we're passing to stage 6
            print(f"[DEBUG execute_stage] Stage 6 arg[1] (outline_output) type: {type(args[1])}")
            if isinstance(args[1], dict):
                print(f"[DEBUG execute_stage] Stage 6 arg[1] keys: {list(args[1].keys())}")
                print(f"[DEBUG execute_stage] Stage 6 arg[1] has 'outline': {'outline' in args[1]}")
        
        output = stage_func(*args, **kwargs)
        
        # Save stage output
        db.save_stage_output(pipeline_id, stage_num, output)
        db.update_pipeline_stage(pipeline_id, stage_num)
        
        # Log success
        db.log_audit_event(
            pipeline_id,
            f'stage_{stage_num}_completed',
            metadata={'success': output.get('success', False)}
        )
        
        if not output.get('success', False):
            error_msg = output.get('error', 'Unknown error')
            print(f"[DEBUG execute_stage] Stage {stage_num} failed with error: {error_msg}")
            raise Exception(f"Stage {stage_num} reported failure: {error_msg}")
        
        print(f"✓ Stage {stage_num} completed successfully")
        
        return output
        
    except Exception as e:
        print(f"✗ Stage {stage_num} failed: {str(e)}")
        traceback.print_exc()
        
        # Log failure
        error_output = {
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }
        
        db.save_stage_output(pipeline_id, stage_num, error_output)
        db.log_audit_event(
            pipeline_id,
            f'stage_{stage_num}_failed',
            metadata={'error': str(e)}
        )
        
        raise


def run_pipeline(source_url: str) -> str:
    """
    Run complete content pipeline
    
    Args:
        source_url: Competitor blog URL
        
    Returns:
        Pipeline ID
    """
    # Validate URL
    if not validate_url(source_url):
        raise ValueError(f"Invalid URL: {source_url}")
    
    # Generate pipeline ID
    pipeline_id = str(uuid.uuid4())
    
    print(f"\n{'#'*60}")
    print(f"# Starting Content Intelligence Pipeline")
    print(f"# Pipeline ID: {pipeline_id}")
    print(f"# Source URL: {source_url}")
    print(f"# Started: {datetime.utcnow().isoformat()}")
    print(f"{'#'*60}\n")
    
    try:
        # Initialize pipeline in database
        db.create_pipeline(pipeline_id, source_url)
        
        # Stage 1: Content Extraction
        stage1_output = execute_stage(
            pipeline_id, 1,
            stage1_extract.run,
            pipeline_id, source_url
        )
        
        # Stage 2: Content Intelligence Analysis
        stage2_output = execute_stage(
            pipeline_id, 2,
            stage2_analyze.run,
            pipeline_id, stage1_output
        )
        
        # Stage 3: Safety & Ethics Gate
        stage3_output = execute_stage(
            pipeline_id, 3,
            stage3_safety.run,
            pipeline_id, stage1_output
        )
        
        # Check safety decision
        safety_decision = stage3_output['decision']['risk_level']
        db.update_pipeline_status(pipeline_id, 'running', safety_decision=safety_decision)
        
        if not stage3_output['decision']['proceed']:
            print("\n🛑 PIPELINE HALTED: Safety gate blocked progression")
            db.update_pipeline_status(pipeline_id, 'blocked_safety')
            return pipeline_id
        
        # Stage 4: Brand Voice RAG Setup (ensure it's initialized)
        # This is typically a one-time setup, but we'll ensure it's ready
        print("\nEnsuring brand voice database is ready...")
        stage4_rag_setup.run()
        
        # Stage 5: Outline Generation
        stage5_output = execute_stage(
            pipeline_id, 5,
            stage5_outline.run,
            pipeline_id, stage2_output
        )
        
        # Stage 6: Full Draft Generation
        # DEBUG: Verify stage5_output before passing to stage6
        print(f"\n[DEBUG Main] Stage 5 output type: {type(stage5_output)}")
        print(f"[DEBUG Main] Stage 5 output keys: {list(stage5_output.keys()) if isinstance(stage5_output, dict) else 'NOT A DICT'}")
        print(f"[DEBUG Main] Stage 5 has 'outline': {'outline' in stage5_output if isinstance(stage5_output, dict) else 'N/A'}")
        
        stage6_output = execute_stage(
            pipeline_id, 6,
            stage6_generate.run,
            pipeline_id, stage5_output, stage2_output
        )
        
        # Stage 7: Quality Assurance
        stage7_output = execute_stage(
            pipeline_id, 7,
            stage7_qa.run,
            pipeline_id, stage6_output
        )
        
        # Check QA results
        quality_report = stage7_output['quality_report']
        quality_score = quality_report['scores']['seo_score']
        
        db.update_pipeline_status(
            pipeline_id,
            'running',
            quality_score=quality_score
        )
        
        if quality_report['overall_status'] == 'BLOCKED':
            print("\n⚠ QUALITY CHECK BLOCKED: Content requires regeneration")
            print("Blocking issues:")
            for issue in quality_report['blocking_issues']:
                print(f"  - {issue}")
            
            db.update_pipeline_status(pipeline_id, 'blocked_qa')
            return pipeline_id
        
        # Stage 8: HTML Formatting
        stage8_output = execute_stage(
            pipeline_id, 8,
            stage8_format.run,
            pipeline_id, stage6_output, stage7_output
        )
        
        # Pipeline complete - mark for human review
        status = 'review_required' if stage3_output['decision']['requires_human_review'] else 'completed'
        db.update_pipeline_status(pipeline_id, status)
        
        print(f"\n{'#'*60}")
        print(f"# Pipeline Completed Successfully!")
        print(f"# Status: {status}")
        print(f"# Quality Score: {quality_score:.1f}/100")
        print(f"# Output HTML: {stage8_output.get('html_file', 'N/A')}")
        print(f"{'#'*60}\n")
        
        # Log completion
        db.log_audit_event(
            pipeline_id,
            'pipeline_completed',
            metadata={
                'quality_score': quality_score,
                'safety_decision': safety_decision,
                'requires_review': stage3_output['decision']['requires_human_review']
            }
        )
        
        return pipeline_id
        
    except Exception as e:
        print(f"\n✗ PIPELINE FAILED: {str(e)}")
        db.update_pipeline_status(pipeline_id, 'failed')
        db.log_audit_event(
            pipeline_id,
            'pipeline_failed',
            metadata={'error': str(e)}
        )
        raise


def get_pipeline_outputs(pipeline_id: str) -> Dict[int, Dict[str, Any]]:
    """
    Get all stage outputs for a pipeline
    
    Args:
        pipeline_id: Pipeline identifier
        
    Returns:
        Dictionary mapping stage numbers to outputs
    """
    return db.get_all_stage_outputs(pipeline_id)


def recover_pipeline(pipeline_id: str, from_stage: int) -> str:
    """
    Recover a failed pipeline from a specific stage
    
    Args:
        pipeline_id: Pipeline identifier
        from_stage: Stage to restart from
        
    Returns:
        Pipeline ID
    """
    print(f"Recovering pipeline {pipeline_id} from stage {from_stage}")
    
    # Get pipeline state
    state = db.get_pipeline_state(pipeline_id)
    if not state:
        raise ValueError(f"Pipeline {pipeline_id} not found")
    
    # Get previous outputs
    outputs = db.get_all_stage_outputs(pipeline_id)
    
    # Continue from specified stage
    # This is a simplified version - full implementation would handle all stages
    raise NotImplementedError("Pipeline recovery not yet implemented")


def main():
    """Main CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Content Intelligence Pipeline')
    parser.add_argument('--url', type=str, help='Competitor blog URL to process')
    parser.add_argument('--setup-db', action='store_true', help='Initialize database')
    parser.add_argument('--setup-rag', action='store_true', help='Setup brand voice RAG')
    parser.add_argument('--list', action='store_true', help='List recent pipelines')
    parser.add_argument('--load', type=str, help='Load pipeline by ID')
    
    args = parser.parse_args()
    
    # Initialize database
    db.init_database()
    
    if args.setup_db:
        print("✓ Database initialized")
        return
    
    if args.setup_rag:
        print("Setting up brand voice database...")
        result = stage4_rag_setup.run()
        print(f"✓ {result['message']}")
        return
    
    if args.list:
        pipelines = db.list_pipelines(limit=20)
        print(f"\nRecent Pipelines ({len(pipelines)}):")
        print("-" * 80)
        for p in pipelines:
            print(f"ID: {p['id']}")
            print(f"  URL: {p['source_url']}")
            print(f"  Status: {p['status']}")
            print(f"  Created: {p['created_at']}")
            print(f"  Safety: {p['safety_decision'] or 'N/A'}")
            print(f"  Quality: {p['quality_score'] or 'N/A'}")
            print()
        return
    
    if args.load:
        state = db.get_pipeline_state(args.load)
        if state:
            print(f"Pipeline {args.load}:")
            print(f"  Status: {state['status']}")
            print(f"  Current Stage: {state['current_stage']}")
            print(f"  Safety: {state['safety_decision']}")
            print(f"  Quality: {state['quality_score']}")
            
            outputs = get_pipeline_outputs(args.load)
            print(f"  Completed Stages: {', '.join(map(str, outputs.keys()))}")
        else:
            print(f"Pipeline {args.load} not found")
        return
    
    if args.url:
        try:
            pipeline_id = run_pipeline(args.url)
            print(f"\n✓ Pipeline ID: {pipeline_id}")
            print(f"\nTo review in dashboard, run:")
            print(f"  streamlit run dashboard/app.py")
        except Exception as e:
            print(f"\n✗ Pipeline failed: {str(e)}")
            sys.exit(1)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()

