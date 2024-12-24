from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import stripe
import braintree
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Stripe Configuration
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

# Braintree Configuration
gateway = braintree.BraintreeGateway(
    braintree.Configuration(
        environment=braintree.Environment.Sandbox,  # Change to Production in live
        merchant_id=os.getenv("BRAINTREE_MERCHANT_ID"),
        public_key=os.getenv("BRAINTREE_PUBLIC_KEY"),
        private_key=os.getenv("BRAINTREE_PRIVATE_KEY")
    )
)

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome! Send your card details in the format: \n\n"
                                    "`Card Number|Exp Month|Exp Year|CVV`",
                                    parse_mode="Markdown")

# Card validation handler
async def validate_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message.text.strip()
    try:
        card_number, exp_month, exp_year, cvv = message.split('|')

        # Stripe validation
        try:
            stripe.Token.create(
                card={
                    "number": card_number,
                    "exp_month": int(exp_month),
                    "exp_year": int(exp_year),
                    "cvc": cvv,
                }
            )
            stripe_status = "Valid"
        except stripe.error.CardError as e:
            stripe_status = f"Invalid - {e.user_message}"

        # Braintree validation
        try:
            result = gateway.credit_card.create({
                "number": card_number,
                "expiration_month": exp_month,
                "expiration_year": exp_year,
                "cvv": cvv
            })
            braintree_status = "Valid" if result.is_success else f"Invalid - {result.message}"
        except Exception as e:
            braintree_status = f"Invalid - {str(e)}"

        # Send response
        await update.message.reply_text(f"**Stripe Status**: {stripe_status}\n"
                                        f"**Braintree Status**: {braintree_status}",
                                        parse_mode="Markdown")
    except ValueError:
        await update.message.reply_text("Invalid format! Please use: `Card Number|Exp Month|Exp Year|CVV`",
                                        parse_mode="Markdown")

# Main function
def main():
    app = ApplicationBuilder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, validate_card))

    print("Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
