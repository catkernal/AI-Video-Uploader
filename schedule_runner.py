"""
Automated Scheduler for Kids Dance Shorts
Runs the full pipeline everyday at 08:01 AM.
"""
import time
import datetime
from main import run_pipeline

# Daily target run time (08:01 AM)
TARGET_HOUR = 8
TARGET_MINUTE = 1

def seconds_until_target(target_hour=TARGET_HOUR, target_minute=TARGET_MINUTE):
    """
    Calculates the exact number of seconds until the next target time (08:01 AM).
    If 08:01 AM has already passed today, it targets tomorrow's 08:01 AM.
    """
    now = datetime.datetime.now()
    target_today = now.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
    
    if now < target_today:
        target_time = target_today
    else:
        target_time = target_today + datetime.timedelta(days=1)
        
    delta_seconds = (target_time - now).total_seconds()
    return delta_seconds, target_time

def start_scheduler():
    run_count = 1
    
    print("⏰ Kids Dance Shorts Scheduler Activated!")
    print(f"Daily Target: Everyday at {TARGET_HOUR:02d}:{TARGET_MINUTE:02d} AM.")
    
    while True:
        wait_seconds, next_run = seconds_until_target()
        hours, rem = divmod(int(wait_seconds), 3600)
        minutes, seconds = divmod(rem, 60)
        
        print(f"\n⏳ Next run scheduled for: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"💤 Sleeping for {hours}h {minutes}m {seconds}s until 08:01 AM...")
        
        time.sleep(wait_seconds)
        
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n[{now_str}] 🚀 Triggering Scheduled Video #{run_count}...")
        
        try:
            result = run_pipeline(auto_upload=True, privacy="public")
            if result:
                print(f"✅ Video #{run_count} successfully produced and uploaded!")
                run_count += 1
            else:
                print(f"⚠️ Video #{run_count} generation failed. Upload skipped.")
        except Exception as e:
            print(f"⚠️ Error during scheduled run: {e}")
            
        # Short cooldown to prevent duplicate triggers within the same minute
        time.sleep(60)

if __name__ == "__main__":
    start_scheduler()
