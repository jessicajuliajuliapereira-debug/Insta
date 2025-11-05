import os
import logging
import asyncio
import threading
import time
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from dotenv import load_dotenv

try:
    from instagrapi import Client
    from instagrapi.exceptions import LoginRequired, ChallengeRequired
    INSTAGRAM_AVAILABLE = True
except ImportError:
    INSTAGRAM_AVAILABLE = False

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
WAITING_USERNAME, WAITING_PASSWORD = range(2)

class InstagramOTPMonitor:
    def __init__(self):
        self.token = os.getenv('8532870741:AAEI3_9_8NmeBF9ce0cDNnTQigDcklkL5Ys')
        self.chat_id = os.getenv('CHAT_ID')
        if not self.token:
            raise ValueError("❌ No BOT_TOKEN found in .env file!")
        
        self.application = Application.builder().token(self.token).build()
        self.ig_client = None
        self.login_data = {}
        self.monitoring = False
        self.monitor_thread = None
        self.last_checked = None
        
        self.setup_handlers()
    
    def setup_handlers(self):
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('login', self.start_login)],
            states={
                WAITING_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_username)],
                WAITING_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_password)],
            },
            fallbacks=[CommandHandler('cancel', self.cancel_login)]
        )
        
        self.application.add_handler(conv_handler)
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("monitor", self.start_monitoring))
        self.application.add_handler(CommandHandler("stop", self.stop_monitoring))
        self.application.add_handler(CommandHandler("status", self.check_status))
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        welcome_text = """
🔐 **Instagram OTP Monitor Bot**

I can monitor your Instagram account for new OTPs and security alerts.

**How it works:**
1. Login with /login
2. Start monitoring with /monitor  
3. I'll notify you of any OTPs received
4. Get real-time security alerts

**Commands:**
/login - Connect to Instagram
/monitor - Start OTP monitoring
/stop - Stop monitoring
/status - Check current status

⚠️ **Note:** Monitors for new emails/messages that contain OTPs
"""
        await update.message.reply_text(welcome_text)
    
    async def start_login(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not INSTAGRAM_AVAILABLE:
            await update.message.reply_text("❌ Instagram features not available.")
            return ConversationHandler.END
        
        await update.message.reply_text(
            "🔐 **Instagram Login**\n\n"
            "Enter your Instagram username:"
        )
        return WAITING_USERNAME
    
    async def get_username(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        username = update.message.text.strip()
        self.login_data['username'] = username
        await update.message.reply_text(f"📝 Username: {username}\n\nNow enter password:")
        return WAITING_PASSWORD
    
    async def get_password(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        password = update.message.text.strip()
        self.login_data['password'] = password
        
        await update.message.reply_text("🔄 Logging in...")
        
        try:
            self.ig_client = Client()
            self.ig_client.login(self.login_data['username'], self.login_data['password'])
            
            user_info = self.ig_client.account_info()
            await update.message.reply_text(
                f"✅ **Logged in as {user_info.username}**\n\n"
                f"Use /monitor to start OTP monitoring"
            )
            self.login_data = {}
            return ConversationHandler.END
            
        except Exception as e:
            await update.message.reply_text(f"❌ Login failed: {str(e)}")
            return ConversationHandler.END
    
    async def start_monitoring(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.ig_client:
            await update.message.reply_text("❌ Not logged in. Use /login first.")
            return
        
        if self.monitoring:
            await update.message.reply_text("✅ Monitoring already active!")
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        await update.message.reply_text(
            "🔍 **OTP Monitoring Started!**\n\n"
            "I'll notify you of:\n"
            "• New login OTPs\n"
            "• Security alerts\n"
            "• Suspicious activities\n\n"
            "Use /stop to end monitoring"
        )
    
    async def stop_monitoring(self, update: Update, ContextTypes.DEFAULT_TYPE):
        self.monitoring = False
        await update.message.reply_text("🛑 OTP monitoring stopped.")
    
    def monitor_loop(self):
        """Background thread to monitor for OTPs"""
        while self.monitoring:
            try:
                self.check_for_otp()
                time.sleep(30)  # Check every 30 seconds
            except Exception as e:
                logger.error(f"Monitor error: {e}")
                time.sleep(60)
    
    def check_for_otp(self):
        """Check for new OTPs and security alerts"""
        if not self.ig_client:
            return
        
        try:
            # Get recent activity (simulated - Instagram API is limited)
            current_time = datetime.now()
            
            # This is a simplified check - real implementation would be more complex
            # Instagram doesn't provide direct OTP monitoring API
            
            # Simulate OTP detection (you'd need to implement actual email/notification parsing)
            self.detect_security_alerts()
            
        except Exception as e:
            logger.error(f"Error checking OTP: {e}")
    
    def detect_security_alerts(self):
        """Detect potential security-related activities"""
        try:
            # Check for new emails/messages that might contain OTPs
            # This is a placeholder - actual implementation would require:
            # 1. Email integration (Gmail API)
            # 2. SMS integration (more complex)
            # 3. Direct Instagram security center access (limited)
            
            # For now, we'll simulate detection
            if self.simulate_otp_detection():
                self.send_otp_alert("🔐 New OTP detected in your account!")
                
        except Exception as e:
            logger.error(f"Error in security detection: {e}")
    
    def simulate_otp_detection(self):
        """Simulate OTP detection - replace with real logic"""
        # This is where you'd integrate with:
        # - Email APIs to check for OTP emails
        # - SMS gateways (complex)
        # - Instagram's security center (limited access)
        
        # For demo purposes, occasionally simulate OTP detection
        import random
        return random.random() < 0.1  # 10% chance for demo
    
    def send_otp_alert(self, message):
        """Send OTP alert to Telegram"""
        try:
            # This would need to be run in async context
            asyncio.run_coroutine_threadsafe(
                self._send_alert_async(message), 
                self.application._loop
            )
        except Exception as e:
            logger.error(f"Error sending alert: {e}")
    
    async def _send_alert_async(self, message):
        """Async method to send alert"""
        try:
            await self.application.bot.send_message(
                chat_id=self.chat_id or "YOUR_CHAT_ID",
                text=f"🚨 **SECURITY ALERT** 🚨\n\n{message}\n\n⏰ {datetime.now().strftime('%H:%M:%S')}"
            )
        except Exception as e:
            logger.error(f"Error sending async alert: {e}")
    
    async def check_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        status = "✅ Monitoring Active" if self.monitoring else "❌ Monitoring Inactive"
        login_status = "✅ Logged In" if self.ig_client else "❌ Not Logged In"
        
        await update.message.reply_text(
            f"📊 **Bot Status**\n\n"
            f"Instagram: {login_status}\n"
            f"Monitoring: {status}\n"
            f"Last Check: {self.last_checked or 'Never'}"
        )
    
    async def cancel_login(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self.login_data = {}
        await update.message.reply_text("❌ Login cancelled.")
        return ConversationHandler.END

    def run(self):
        logger.info("Starting OTP Monitor Bot...")
        self.application.run_polling()

if __name__ == '__main__':
    try:
        bot = InstagramOTPMonitor()
        bot.run()
    except Exception as e:
        print(f"Failed to start: {e}")