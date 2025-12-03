from src.core.logger_config import get_logger

logger = get_logger(__name__)
"""
Reminder Manager for JARVIS
Supports one-time reminders, recurring reminders, and timers
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import threading
import time


class ReminderManager:
    """
    Manage reminders and timers for JARVIS
    
    Features:
    - One-time reminders ("Remind me to call John at 3pm")
    - Recurring reminders ("Remind me to exercise every day at 7am")
    - Timers ("Set a timer for 10 minutes")
    - Desktop notifications
    - Persistent storage
    """
    
    def __init__(self, reminders_file="reminders.json"):
        """
        Initialize reminder manager
        
        Args:
            reminders_file: Path to JSON file for storing reminders
        """
        self.reminders_file = reminders_file
        self.reminders = []
        self.timers = []
        self.running = False
        self.check_thread = None
        
        # Load existing reminders
        self.load_reminders()
        
        logger.info("[Reminders] Reminder manager initialized")
    
    def load_reminders(self):
        """Load reminders from file"""
        if os.path.exists(self.reminders_file):
            try:
                with open(self.reminders_file, 'r') as f:
                    data = json.load(f)
                    self.reminders = data.get('reminders', [])
                    # Clean up past one-time reminders
                    self._cleanup_old_reminders()
                logger.info(f"[Reminders] Loaded {len(self.reminders)} reminders")
            except Exception as e:
                logger.error(f"[Reminders] Error loading reminders: {e}")
                self.reminders = []
        else:
            self.reminders = []
    
    def save_reminders(self):
        """Save reminders to file"""
        try:
            with open(self.reminders_file, 'w') as f:
                json.dump({
                    'reminders': self.reminders
                }, f, indent=2)
        except Exception as e:
            logger.error(f"[Reminders] Error saving reminders: {e}")
    
    def _cleanup_old_reminders(self):
        """Remove old one-time reminders that have already triggered"""
        now = datetime.now()
        original_count = len(self.reminders)
        
        self.reminders = [
            r for r in self.reminders
            if r.get('recurring') or datetime.fromisoformat(r['time']) > now
        ]
        
        removed = original_count - len(self.reminders)
        if removed > 0:
            logger.info(f"[Reminders] Cleaned up {removed} old reminders")
            self.save_reminders()
    
    def add_reminder(self, text, time_str, recurring=None):
        """
        Add a new reminder
        
        Args:
            text: Reminder text
            time_str: Time string (ISO format or parsed datetime)
            recurring: Recurrence pattern ('daily', 'weekly', 'monthly', None)
            
        Returns:
            dict: Success status and message
        """
        try:
            # Parse time if it's a string
            if isinstance(time_str, str):
                reminder_time = datetime.fromisoformat(time_str)
            elif isinstance(time_str, datetime):
                reminder_time = time_str
            else:
                return {
                    "success": False,
                    "message": "Invalid time format"
                }
            
            # Check if time is in the past (for one-time reminders)
            if not recurring and reminder_time < datetime.now():
                return {
                    "success": False,
                    "message": "Cannot set reminder in the past"
                }
            
            # Create reminder
            reminder = {
                'id': len(self.reminders) + 1,
                'text': text,
                'time': reminder_time.isoformat(),
                'recurring': recurring,
                'active': True,
                'created_at': datetime.now().isoformat()
            }
            
            self.reminders.append(reminder)
            self.save_reminders()
            
            # Format response
            time_str = reminder_time.strftime("%I:%M %p on %B %d")
            if recurring:
                return {
                    "success": True,
                    "message": f"Reminder set: '{text}' {recurring} at {reminder_time.strftime('%I:%M %p')}"
                }
            else:
                return {
                    "success": True,
                    "message": f"Reminder set: '{text}' at {time_str}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "message": f"Error setting reminder: {e}"
            }
    
    def add_timer(self, duration_minutes, label="Timer"):
        """
        Add a countdown timer
        
        Args:
            duration_minutes: Duration in minutes
            label: Timer label
            
        Returns:
            dict: Success status and message
        """
        try:
            end_time = datetime.now() + timedelta(minutes=duration_minutes)
            
            timer = {
                'id': len(self.timers) + 1,
                'label': label,
                'duration_minutes': duration_minutes,
                'end_time': end_time.isoformat(),
                'active': True
            }
            
            self.timers.append(timer)
            
            return {
                "success": True,
                "message": f"Timer set for {duration_minutes} minutes"
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Error setting timer: {e}"
            }
    
    def get_active_reminders(self):
        """Get all active reminders"""
        return [r for r in self.reminders if r.get('active', True)]
    
    def get_upcoming_reminders(self, hours=24):
        """
        Get reminders due in the next N hours
        
        Args:
            hours: Number of hours to look ahead
            
        Returns:
            list: Upcoming reminders
        """
        now = datetime.now()
        cutoff = now + timedelta(hours=hours)
        
        upcoming = []
        for reminder in self.get_active_reminders():
            reminder_time = datetime.fromisoformat(reminder['time'])
            
            if now <= reminder_time <= cutoff:
                upcoming.append(reminder)
            elif reminder.get('recurring'):
                # Check if recurring reminder is due today
                next_occurrence = self._get_next_occurrence(reminder)
                if next_occurrence and now <= next_occurrence <= cutoff:
                    upcoming.append(reminder)
        
        return sorted(upcoming, key=lambda r: r['time'])
    
    def _get_next_occurrence(self, reminder):
        """Calculate next occurrence for recurring reminder"""
        if not reminder.get('recurring'):
            return None
        
        reminder_time = datetime.fromisoformat(reminder['time'])
        now = datetime.now()
        recurring = reminder['recurring']
        
        # Start from the original time
        next_time = reminder_time
        
        # Advance to next occurrence
        while next_time < now:
            if recurring == 'daily':
                next_time += timedelta(days=1)
            elif recurring == 'weekly':
                next_time += timedelta(weeks=1)
            elif recurring == 'monthly':
                # Approximate month as 30 days
                next_time += timedelta(days=30)
            else:
                return None
        
        return next_time
    
    def delete_reminder(self, reminder_id):
        """
        Delete a reminder by ID
        
        Args:
            reminder_id: ID of reminder to delete
            
        Returns:
            dict: Success status and message
        """
        for i, reminder in enumerate(self.reminders):
            if reminder['id'] == reminder_id:
                deleted = self.reminders.pop(i)
                self.save_reminders()
                return {
                    "success": True,
                    "message": f"Deleted reminder: {deleted['text']}"
                }
        
        return {
            "success": False,
            "message": f"Reminder {reminder_id} not found"
        }
    
    def snooze_reminder(self, reminder_id, minutes=10):
        """
        Snooze a reminder
        
        Args:
            reminder_id: ID of reminder to snooze
            minutes: Minutes to snooze
            
        Returns:
            dict: Success status and message
        """
        for reminder in self.reminders:
            if reminder['id'] == reminder_id:
                old_time = datetime.fromisoformat(reminder['time'])
                new_time = old_time + timedelta(minutes=minutes)
                reminder['time'] = new_time.isoformat()
                self.save_reminders()
                
                return {
                    "success": True,
                    "message": f"Snoozed for {minutes} minutes"
                }
        
        return {
            "success": False,
            "message": f"Reminder {reminder_id} not found"
        }
    
    def check_reminders(self):
        """Check for due reminders and timers"""
        now = datetime.now()
        triggered = []
        
        # Check reminders
        for reminder in self.get_active_reminders():
            reminder_time = datetime.fromisoformat(reminder['time'])
            
            # Check if reminder is due
            if now >= reminder_time:
                triggered.append({
                    'type': 'reminder',
                    'text': reminder['text'],
                    'id': reminder['id']
                })
                
                # Handle recurring vs one-time
                if reminder.get('recurring'):
                    # Update to next occurrence
                    next_time = self._get_next_occurrence(reminder)
                    if next_time:
                        reminder['time'] = next_time.isoformat()
                else:
                    # Deactivate one-time reminder
                    reminder['active'] = False
                
                self.save_reminders()
        
        # Check timers
        for timer in self.timers[:]:  # Copy list to allow removal
            if not timer.get('active'):
                continue
                
            end_time = datetime.fromisoformat(timer['end_time'])
            
            if now >= end_time:
                triggered.append({
                    'type': 'timer',
                    'text': f"{timer['label']} - {timer['duration_minutes']} minutes",
                    'id': timer['id']
                })
                
                # Remove timer
                timer['active'] = False
                self.timers.remove(timer)
        
        return triggered
    
    def start_background_checker(self, callback=None):
        """
        Start background thread to check reminders
        
        Args:
            callback: Function to call when reminder triggers
        """
        if self.running:
            logger.info("[Reminders] Background checker already running")
            return
        
        self.running = True
        
        def check_loop():
            logger.info("[Reminders] Background checker started")
            while self.running:
                try:
                    triggered = self.check_reminders()
                    
                    for item in triggered:
                        logger.info(f"[Reminders] TRIGGERED: {item['text']}")
                        
                        # Call callback if provided
                        if callback:
                            callback(item)
                        else:
                            # Default: show notification
                            self._show_notification(item)
                    
                    # Check every 30 seconds
                    time.sleep(30)
                    
                except Exception as e:
                    logger.error(f"[Reminders] Error in check loop: {e}")
                    time.sleep(30)
        
        self.check_thread = threading.Thread(target=check_loop, daemon=True)
        self.check_thread.start()
    
    def stop_background_checker(self):
        """Stop background checker"""
        self.running = False
        if self.check_thread:
            self.check_thread.join(timeout=2)
        logger.info("[Reminders] Background checker stopped")
    
    def _show_notification(self, item):
        """Show desktop notification"""
        try:
            from plyer import notification
            
            title = "JARVIS Reminder" if item['type'] == 'reminder' else "JARVIS Timer"
            
            notification.notify(
                title=title,
                message=item['text'],
                app_name='JARVIS',
                timeout=10
            )
        except ImportError:
            logger.info("[Reminders] plyer not installed - notifications disabled")
            logger.info(f"[Reminders] {item['type'].upper()}: {item['text']}")
        except Exception as e:
            logger.error(f"[Reminders] Notification error: {e}")
    
    def get_summary(self):
        """Get summary of all reminders and timers"""
        active_reminders = self.get_active_reminders()
        active_timers = [t for t in self.timers if t.get('active')]
        
        summary = f"You have {len(active_reminders)} active reminders"
        
        if active_timers:
            summary += f" and {len(active_timers)} active timers"
        
        return summary
    
    def list_reminders(self):
        """Get formatted list of all reminders"""
        active = self.get_active_reminders()
        
        if not active:
            return "No active reminders"
        
        lines = ["Your reminders:"]
        for i, reminder in enumerate(active, 1):
            reminder_time = datetime.fromisoformat(reminder['time'])
            time_str = reminder_time.strftime("%I:%M %p on %B %d")
            
            recurring_str = f" ({reminder['recurring']})" if reminder.get('recurring') else ""
            lines.append(f"{i}. {reminder['text']} - {time_str}{recurring_str}")
        
        return "\n".join(lines)


if __name__ == "__main__":
    # Test the reminder manager
    logger.info("="*70)
    logger.info("  Reminder Manager Test")
    logger.info("="*70)
    
    rm = ReminderManager("test_reminders.json")
    
    # Add some test reminders
    logger.info("\n[1] Adding reminders...")
    
    # One-time reminder (5 minutes from now)
    future_time = datetime.now() + timedelta(minutes=5)
    result = rm.add_reminder("Call John", future_time)
    logger.info(f"  {result['message']}")
    
    # Recurring reminder
    tomorrow_9am = datetime.now().replace(hour=9, minute=0, second=0) + timedelta(days=1)
    result = rm.add_reminder("Take medicine", tomorrow_9am, recurring='daily')
    logger.info(f"  {result['message']}")
    
    # Timer
    result = rm.add_timer(1, "Test timer")
    logger.info(f"  {result['message']}")
    
    # List reminders
    logger.info("\n[2] Current reminders:")
    print(rm.list_reminders())
    
    # Summary
    logger.info("\n[3] Summary:")
    print(rm.get_summary())
    
    # Cleanup
    import os
    if os.path.exists("test_reminders.json"):
        os.remove("test_reminders.json")
    
    logger.info("\n" + "="*70)
    logger.info("Test complete!")
    logger.info("="*70)
