# src/campaign_manager.py
from datetime import datetime, timedelta
from src import data_manager
from src.data_manager import Lead, Campaign, CampaignStep, get_db

def create_campaign(name, steps_data, user_id):
    """
    Creates a new campaign with steps.
    steps_data: List of dicts, e.g., [{"step_number": 1, "day_delay": 0, "subject": "...", "body": "..."}]
    """
    db = next(get_db())
    try:
        # Check if exists for THIS user
        exists = db.query(Campaign).filter_by(user_id=user_id, name=name).first()
        if exists:
            print(f"Campaign '{name}' already exists for user {user_id}.")
            return exists
            
        # Create Campaign
        campaign = Campaign(name=name, status="Active", user_id=user_id)
        db.add(campaign)
        db.commit()
        db.refresh(campaign)
        
        # Create Steps
        for index, step in enumerate(steps_data):
            new_step = CampaignStep(
                campaign_id=campaign.id,
                step_number=index + 1,
                delay_days=step.get('delay', 2),
                subject_template=step.get('subject', ''),
                body_template=step.get('body', '')
            )
            db.add(new_step)
        
        db.commit()
        db.refresh(campaign)
        db.expunge(campaign) # Detach so it can be used after session close
        return campaign
    except Exception as e:
        print(f"[ERROR] Create Campaign Failed: {e}")
        db.rollback()
        return None
    finally:
        db.close()

def enroll_leads(campaign_id, limit=50):
    """
    Enrolls new leads into a campaign.
    """
    db = next(get_db())
    try:
        # Find leads not in any campaign
        leads = db.query(Lead).filter(Lead.campaign_id == None).limit(limit).all()
        
        count = 0
        for lead in leads:
            lead.campaign_id = campaign_id
            lead.current_step = 1
            lead.next_action_at = datetime.utcnow() # Ready immediately for Step 1
            count += 1
            
        db.commit()
        print(f"[INFO] Enrolled {count} leads into Campaign {campaign_id}")
        return count
    finally:
        db.close()

def get_due_leads():
    """
    Returns leads that are ready for their next step.
    """
    db = next(get_db())
    try:
        now = datetime.utcnow()
        # Find leads where next_action_at is past, status is not Replied/Completed
        leads = db.query(Lead).filter(
            Lead.next_action_at <= now,
            Lead.status.notin_(['Replied', 'Bounced', 'Completed']),
            Lead.campaign_id != None
        ).all()
        
        results = []
        for lead in leads:
            # Fetch the actual step template
            step = db.query(CampaignStep).filter_by(
                campaign_id=lead.campaign_id, 
                step_number=lead.current_step
            ).first()
            
            if step:
                results.append({
                    "lead_obj": lead, # Pass ORM object for updates
                    "email": lead.email,
                    "name": lead.name,
                    "company": lead.company,
                    "personalization": lead.personalization_line,
                    "subject": step.subject_template,
                    "body_template": step.body_template,
                    "step_number": lead.current_step,
                    "step_delay": step.delay_days
                })
        return results
    finally:
        db.close()

def advance_lead(lead_id):
    """
    Moves a lead to the next step after sending.
    """
    db = next(get_db())
    try:
        lead = db.query(Lead).filter_by(id=lead_id).first()
        if not lead: return
        
        # Check if there is a next step
        current_step = lead.current_step
        next_step_num = current_step + 1
        
        next_step = db.query(CampaignStep).filter_by(
            campaign_id=lead.campaign_id, 
            step_number=next_step_num
        ).first()
        
        if next_step:
            lead.current_step = next_step_num
            # Schedule next email based on delay
            lead.next_action_at = datetime.utcnow() + timedelta(days=next_step.delay_days)
            lead.status = "Contacted"
        else:
            # Sequence complete
            lead.status = "Completed"
            lead.next_action_at = None
            
        lead.last_contacted_at = datetime.utcnow()
        db.commit()
    finally:
        db.close()
