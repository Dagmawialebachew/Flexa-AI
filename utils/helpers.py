TEXTS = {
    'welcome': {
        'en': '🎨 *Welcome to Flexa AI*\n\nTransform your photos with AI magic! Choose a style, upload your photo, and let us create something amazing.\n\n✨ You received *{credits} free credits* to get started!',
        'am': '🎨 *ወደ Flexa AI እንኳን በደህና መጡ*\n\nፎቶዎን በAI ይለውጡ! ስታይል ይምረጡ፣ ፎቶዎን ይላኩ፣ እና አስደናቂ ነገር እንፍጠር።\n\n✨ ለመጀመር *{credits} ነጻ ክሬዲቶች* ተሰጥተውዎታል።'
    },
    'main_menu': {
    'en': '🏠 <b>Main Menu</b>\n\n💎 You have <b>{balance}</b> credits waiting!\nWhat would you like to create today?',
    'am': '🏠 <b>ዋና ማውጫ</b>\n\n💎 <b>{balance}</b> ክሬዲት ቀሪ አለዎት!\n\nእባክዎ ከታች ያሉትን ቁልፎች ይጠቀሙ'
},

    'select_style': {
        'en': '🎨 *Choose Your Style*\n\nSelect how you want to transform your photo:',
        'am': '🎨 *ስታይል ይምረጡ*\n\nፎቶዎን እንዴት መለወጥ እንደሚፈልጉ ይምረጡ፦'
    },
    'upload_photo': {
        'en': "📸 *Upload Your Photo*\n\nSend me the photo you want to transform.\n\nMake sure it's clear and well-lit for best results!",
        'am': "📸 *ፎቶ ይላኩ*\n\nመለወጥ የሚፈልጉትን ፎቶ ይላኩ።\n\nለበለጠ ውጤት ፎቶው ጥራት ያለውና በቂ ብርሃን ያለው መሆኑን ያረጋግጡ!"
    },
    'processing': {
        'en': '⚡ *Processing...*\n\nOur AI is working its magic on your photo. This usually takes 30-60 seconds.',
        'am': '⚡ *በሂደት ላይ...*\n\nAI-ያችን ፎቶዎን እያዘጋጀ ነው። ይህ አብዛኛውን ጊዜ ከ30-60 ሰከንድ ይወስዳል።'
    },
    'success': {
        'en': "✨ *Done!*\n\nHere's your transformed photo. Hope you love it!\n\n💳 Credits used: {credits}\n💰 Remaining: {balance}",
        'am': "✨ *ተጠናቋል!*\n\nየተለወጠው ፎቶዎ ይኸውልዎት። እንደሚወዱት ተስፋ እናደርጋለን!\n\n💳 ጥቅም ላይ የዋለ ክሬዲት: {credits}\n💰 ቀሪ ሂሳብ: {balance}"
    },
    'insufficient_credits': {
        'en': '⚠️ *Insufficient Credits*\n\nYou need {required} credits but have {balance}.\n\nPlease buy more credits to continue!',
        'am': '⚠️ *በቂ ክሬዲት የለም*\n\nቢያንስ {required} ክሬዲቶች ያስፈልጋሉ፤ የእርስዎ ቀሪ ግን {balance} ነው።\n\nእባክዎ ለመቀጠል ተጨማሪ ክሬዲት ይግዙ!'
    },
    'my_credits': {
        'en': '💰 *Your Credits*\n\n💳 Available: *{balance} credits*\n📊 Total generations: {total}\n\nEach generation costs 1-2 credits depending on the style.',
        'am': '💰 *የእርስዎ ክሬዲቶች*\n\n💳 ያሎት ክሬዲት: *{balance}*\n📊 ጠቅላላ የተሰሩ ፎቶዎች: {total}\n\nእያንዳንዱ ፎቶ እንደ ስታይሉ አይነት ከ1-2 ክሬዲት ያስከፍላል።'
    },
    'buy_credits': {
        'en': (
            "💳 *Buy Credits*\n\n"
            "📦 *Available Packages:*\n"
            "   • 🖼️ 5 Images — 100 Birr\n"
            "   • 🖼️ 10 Images — 150 Birr\n"
            "   • 🖼️ 25 Images — 300 Birr\n\n"
            "📝 *Instructions:*\n"
            "   1. Choose your preferred package.\n"
            "   2. Complete the payment.\n"
            "   3. 📸 Send us a screenshot of the confirmation for verification."
        ),
        'am': (
            "💳 *ክሬዲት ይግዙ*\n\n"
            "📦 *ጥቅሎች:*\n"
            "   • 🖼️ ለ 5 ፎቶ — 100 ብር\n"
            "   • 🖼️ ለ 10 ፎቶ — 150 ብር\n"
            "   • 🖼️ ለ 25 ፎቶ — 300 ብር\n\n"
            "📝 *መመሪያ:*\n"
            "   1. የሚፈልጉትን ጥቅል ይምረጡ።\n"
            "   2. ክፍያውን ይፈጽሙ።\n"
            "   3. 📸 ክፍያውን መፈጸምዎን የሚያሳይ ስክሪንሾት ይላኩልን።"
        )
    },
    'payment_submitted': {
        'en': "✅ *Payment Submitted*\n\nYour payment is under review. We'll notify you once it's approved!\n\nUsually takes 5-30 minutes.",
        'am': "✅ *ክፍያ ተልካል*\n\nክፍያዎ እየተረጋገጠ ነው። እንደተፈቀደ እናሳውቅዎታለን!\n\nይህ አብዛኛውን ጊዜ ከ5-30 ደቂቃ ይወስዳል።"
    },
    'error_general': {
        'en': '❌ Something went wrong. Please try again or contact support.',
        'am': '❌ የሆነ ስህተት ተፈጥሯል። እባክዎ እንደገና ይሞክሩ ወይም ድጋፍ ሰጪውን ያነጋግሩ።'
    },
    'help': {
        'en': '📞 *Help & Support*\n\n*How it works:*\n1. Choose a style\n2. Upload your photo\n3. Get AI-transformed result\n\n*Credits:*\n- Each generation costs 1-2 credits\n- Buy credit packages anytime\n\n*Need help?*\nContact @FlexaAISupportbot',
        'am': '📞 *እገዛ እና ድጋፍ*\n\n*እንዴት ይሰራል?*\n1. ስታይል ይምረጡ\n2. ፎቶዎን ይላኩ\n3. በAI የተለወጠ ውጤት ያግኙ\n\n*ስለ ክሬዲት:*\n- ለእያንዳንዱ ፎቶ 1-2 ክሬዲት ይጠየቃል\n- በማንኛውም ሰዓት ክሬዲት መግዛት ይችላሉ\n\n*እገዛ ይፈልጋሉ?*\n@FlexaAISupportbot ን ያነጋግሩ'
    },
    "select_style_preview": {
        "en": "🎨 <b>Choose a style</b>\n\nBrowse a few previews below. Tap a style to view details and a short prompt teaser.\n\nUse ⬅️ / ➡️ to navigate pages.",
        "am": "🎨 <b>ስታይል ይምረጡ</b>\n\nከታች ያሉትን ቅድመ-እይታዎች ይመልከቱ። ዝርዝሩን ለማየት ስታይሉን ይጫኑ።\n\nገጾቹን ለመቀያየር ⬅️ / ➡️ ይጠቀሙ።"
    },
    "already_pending": {
        "en": "⏳ You already have a pending request. Please wait until it's processed before creating another.",
        "am": "⏳ በአሁኑ ሰዓት ከዚ ቀደም ያስገቡትን ክፍያ በመሰራት ላይ ነው። እባክዎ ያሁኑ እስኪጠናቀቅ ይጠብቁ።"
    },
    "browse_styles_page": {
        "en": "🎨 Browse styles — Page {page}",
        "am": "🎨 ስታይሎችን ይመልከቱ — ገጽ {page}"
    },
    "all_styles": {
        "en": "📚 All styles — pick one to view details",
        "am": "📚 ሁሉም ስታይሎች — ዝርዝሩን ለማየት አንዱን ይምረጡ"
    },
    "view_label": {
        "en": "View #{idx} {name}",
        "am": "ተመልከት #{idx} {name}"
    },
    "style_view_caption": {
        "en": "✅ <b>{style_name}</b> {emoji}\n\n{desc}\n\n💎 <b>Cost:</b> {cost} credit{plural}\n\n🧾 <b>Prompt teaser:</b>\n<code>{teaser}</code>\n\n✨ Choose this style to upload your photo and transform it.",
        "am": "✅ <b>{style_name}</b> {emoji}\n\n{desc}\n\n💎 <b>ዋጋ:</b> {cost} ክሬዲት{plural}\n\n🧾 <b>የፕሮምፕት ቅድመ-እይታ:</b>\n<code>{teaser}</code>\n\n✨ ፎቶዎን ለመለወጥ ይህንን ስታይል ይምረጡ።"
    },
    "choose_style_prompt": {
        "en": "🎯 <b>Great choice!</b>\n\nYou picked <b>{name}</b>.\n\n📤 Now upload the photo you want to transform.",
        "am": "🎯 <b>ምርጥ ምርጫ!</b>\n\n<b>{name}</b>ን መርጠዋል።\n\n📤 አሁን መለወጥ የሚፈልጉትን ፎቶ ይላኩ።"
    },
    "ready_receive": {
        "en": "Ready to receive your photo",
        "am": "ፎቶዎን ለመቀበል ዝግጁ ነኝ"
    },
    "style_card_caption": {
        "en": "{emoji} <b>{style_name}</b>\n\n{desc_short}\n\n💎 <b>Cost:</b> {cost} credit{plural}\n\n🧾 <b>Prompt:</b> <code>{teaser}</code>",
        "am": "{emoji} <b>{style_name}</b>\n\n{desc_short}\n\n💎 <b>ዋጋ:</b> {cost} ክሬዲት{plural}\n\n🧾 <b>ፕሮምፕት:</b> <code>{teaser}</code>"
    },
    "manual_queue": {
        "en": "⏳ Our AI is having trouble right now.\n\nNo worries! We've added your request to our **priority queue** and it will be completed manually within *3–10 minutes*.\n\n✅ Your credits have already been deducted.",
        "am": "⏳ በአሁኑ ሰዓት በAI-ያችን ላይ ትንሽ መቆራረጥ አጋጥሟል።\n\nአይጨነቁ! ጥያቄዎ በ**ቅድሚያ ዝርዝር** ውስጥ ተካቷል፤ በአስተዳዳሪዎቻችን አማካኝነት ከ*3–10 ደቂቃ* ባለው ጊዜ ውስጥ ተረክበን እናጠናቅቃለን።\n\n✅ ክሬዲትዎ አስቀድሞ ተቀንሷል።"
    },
    "cancelled": {
        "en": "❌ Cancelled.\n\nBack to main menu.",
        "am": "❌ ተሰርዟል።\n\nወደ ዋና ማውጫ ተመልሷል።"
    },
    "manual_cancelled_user": {
        "en": "❌ *Request cancelled*\n\nYour request has been cancelled.\n\n*Reason:* {reason}\n💳 *Credits refunded:* {credits}\n💰 *New balance:* {balance}",
        "am": "❌ *ጥያቄው ተሰርዟል*\n\nጥያቄዎ ተሰርዟል።\n\n*ምክንያት:* {reason}\n💳 *የተመለሰ ክሬዲት:* {credits}\n💰 *አዲስ ቀሪ ሂሳብ:* {balance}"
    },
    "payment_instructions": {
        "en": "💳 *Payment Instructions*\n\n{instructions}\n\nWhen done, send a screenshot here for verification.",
        "am": "💳 *የክፍያ መመሪያ*\n\n{instructions}\n\nክፍያውን እንደፈጸሙ ማረጋገጫ ስክሪንሾት እዚህ ይላኩ።"
    },
    "upload_payment_prompt": {
        "en": "📸 Please upload a screenshot of your payment to verify your purchase.",
        "am": "📸 እባክዎ ግዢዎን ለማረጋገጥ የክፍያውን ስክሪንሾት ይላኩ።"
    },
    "payment_processing": {
        "en": "⏳ Processing your payment...",
        "am": "⏳ ክፍያዎ እየተመረመረ ነው..."
    },
    "not_authorized": {
        "en": "❌ You are not authorized to use this command.",
        "am": "❌ ይህንን ትዕዛዝ ለመጠቀም ፈቃድ የለዎትም።"
    },
    "manual_queue_empty": {
        "en": "✅ Manual queue is empty. No tasks to process.",
        "am": "✅ የሚጠበቅ ስራ የለም። ዝርዝሩ ባዶ ነው።"
    },
    "manual_queue_header": {
        "en": "Manual Queue",
        "am": "በእጅ የሚሰሩ ስራዎች ዝርዝር"
    },
    "payment_account": {
        "en": "Send to Telebirr 0960306801 → Flexa account",
        "am": "በቴሌብር ወደ 0960306801 (Flexa account) ይላኩ"
    },
    "upload_payment_invalid": {
        "en": "📸 Please upload a valid screenshot of your payment receipt (showing amount and confirmation).",
        "am": "📸 እባክዎ ትክክለኛ የክፍያ ማረጋገጫ ስክሪንሾት ይላኩ (መጠኑን እና የማረጋገጫ ቁጥሩን የሚያሳይ)።"
    },
    "payment_pending_review": {
        "en": "⚠️ You already have a payment under review. Please wait until it is processed.",
        "am": "⚠️ ቀድሞ የላኩት ክፍያ በመረጋገጥ ላይ ነው። እባክዎ ያ እስኪጠናቀቅ ይጠብቁ።"
    },
    "admin_payment_approved": {
        "en": "✅ *Payment Approved*\n\nUser: {user_name}\n💎 Credits Added: {credits}\n💰 New Balance: {balance}",
        "am": "✅ *ክፍያ ተፈቅዷል*\n\nተጠቃሚ: {user_name}\n💎 የተጨመረ ክሬዲት: {credits}\n💰 አዲስ ቀሪ ሂሳብ: {balance}"
    },
    "user_payment_approved": {
        "en": "🎉 *Your payment has been approved!*\n\n💎 {credits} credits have been added.\n💰 New balance: {balance}",
        "am": "🎉 *ክፍያዎ ተረጋግጧል!*\n\n💎 {credits} ክሬዲት ተጨምሮልዎታል።\n💰 አዲስ ቀሪ ሂሳብ: {balance}"
    },
    "admin_payment_rejected_confirm": {
        "en": "❌ Payment {payment_id} rejected.\nReason: {reason}\nCredits NOT added.",
        "am": "❌ ክፍያ {payment_id} ውድቅ ተደርጓል።\nምክንያት: {reason}\nክሬዲት አልተጨመረም።"
    },
    "user_payment_rejected": {
        "en": "❌ *Your payment was rejected*\n\nReason: {reason}\n\nPlease contact support for more information.",
        "am": "❌ *ክፍያዎ ውድቅ ተደርጓል*\n\nምክንያት: {reason}\n\nለተጨማሪ መረጃ እባክዎ ድጋፍ ሰጪውን ያነጋግሩ።"
    },
    "user_banned": {
        "en": "🚫 *Account suspended*\n\nYour account has been suspended by the administrators. If you believe this is a mistake, please contact support.",
        "am": "🚫 *መለያዎ ታግዷል*\n\nመለያዎ በአስተዳዳሪ ታግዷል። ስህተት ነው ብለው ካሰቡ እባክዎ ድጋፍ ሰጪውን ያነጋግሩ።"
    },
    "user_unbanned": {
        "en": "✅ *Account restored*\n\nYour account has been restored. You can now continue using the service.",
        "am": "✅ *መለያዎ ተመልሷል*\n\nመለያዎ ተለቋል። አሁን አገልግሎቱን መጠቀም ይችላሉ።"
    },
    "user_credits_added": {
        "en": "➕ *Credits added*\n\n{credits} credits have been added to your account by an administrator.\n💰 New balance: {balance}",
        "am": "➕ *ክሬዲት ተጨምሯል*\n\nበአስተዳዳሪው {credits} ክሬዲት ተጨምሮልዎታል።\n💰 አዲስ ቀሪ ሂሳብ: {balance}"
    }
}


TEXTS.update({
    "onboarding_join_channel": {
        "en": "🚀 To unlock the bot, please join our channel first 👇",
        "am": "🚀 ቦቱን ለመክፈት እባክዎ በመጀመሪያ ቻናላችንን ይቀላቀሉ 👇"
    },
    "onboarding_thanks_joined": {
        "en": "✅ Thanks for joining! Let’s continue…",
        "am": "✅ እናመሰግናለን ቻናላችንን ተቀላቀሉ። እንቀጥል…"
    },
    "onboarding_still_required": {
        "en": "❌ You still need to join the channel.",
        "am": "❌ እባክዎ በመጀመሪያ ቻናላችንን ይቀላቀሉ።"
    },
    "onboarding_choose_language": {
        "en": "🌐 Choose your language",
        "am": "🌐 ቋንቋ ይምረጡ"
    }
})

TEXTS.update ( 
              {
    "browse_styles_page": {
    "en": "📚 Browsing styles — Page {page}/{total_pages}",
    "am": "📚 ገጽ {page}/{total_pages}"
}})


TEXTS.update({
    "error_throttle_message": {
        "en": "🍲 Too many messages — Flexa got it, no need to flood.",
        "am": "🍲 ብዙ መልዕክቶች እየላኩ ነው፤ ለመመለስ እየሞከርኩ ነው፣ እባክዎ ቃስ ያርጉኝ።"
    },
    "error_throttle_callback": {
        "en": "⏳ Flexa is updating — please don’t tap so fast.",
        "am": "⏳ Flexa AI በማሰብ ላይ ነው፤ እባክዎ በፍጥነት አትጫኑ።"
    }
})




BUTTONS = {
    'generate_photo': {'en': '🎨 Generate Photo', 'am': '🎨 ፎቶ መቀየሪያ'},
    'my_credits': {'en': '🧾 My Credits', 'am': '🧾 የእኔ ክሬዲቶች'},
    'buy_credits': {'en': '💳 Buy Credits', 'am': '💳 ክሬዲት ለመግዛት'},
    'help': {'en': '📞 Help', 'am': '📞 እገዛ/አስተያየት'},
    'settings': {'en': '⚙️ Settings', 'am': '⚙️ ሴቲንግ'},
    'back': {'en': '🔙 Back', 'am': '🔙 ተመለስ'},
    'cancel': {'en': '❌ Cancel', 'am': '❌ ሰርዝ'},
    'change_language': {'en': '🌐 Change Language', 'am': '🌐 ቋንቋ ቀይር'},
    "prev": {"en": "⬅️ Prev", "am": "⬅️ ወደ ኋላ"},
    "next": {"en": "➡️ Next", "am": "➡️ ቀጣይ"},
    "browse_all": {"en": "🔍 Browse All Details", "am": "🔍 ሁሉንም እይ"},
    "choose_style": {"en": "✨ Choose This Style", "am": "✨ ይህንን ስታይል ይምረጡ"},
    "back_to_previews": {"en": "⬅️ Back to previews", "am": "⬅️ ወደ ቅድመ-እይታዎች"},
    "view": {"en": "🔎 View Details", "am": "🔎 ዝርዝር እይ"}
}


BUTTONS.update({
    "join_channel": {
        "en": "📢 Join Flexa Channel",
        "am": "📢 ወደ Flexa ቻናል ተቀላቀሉ"
    },
    "joined_confirm": {
        "en": "✅ I’ve Joined",
        "am": "✅ ተቀላቅያለው"
    }
})


TEXTS.update({
    "settings_menu": {
        "en": "⚙️ *Settings*\n\nChoose what you’d like to adjust:",
        "am": "⚙️ *ሴቲንግ*\n\nምን ማስተካከል ትፈልጋላችሁ?"
    },
    "language_changed": {
        "en": "🌐 *Language updated!*\n\nYour interface is now in English.",
        "am": "🌐 *ቋንቋ ተቀይሯል!*\n\nመለያዎ አሁን በአማርኛ ነው።"
    }
})


# -------------------------
# Localization helpers
# -------------------------
def get_text(key: str, lang: str = 'en', **kwargs) -> str:
    text = TEXTS.get(key, {}).get(lang, TEXTS.get(key, {}).get('en', ''))
    if kwargs:
        # compute plural if requested and not provided
        if 'plural' in text and 'plural' not in kwargs:
            pass
        return text.format(**kwargs)
    return text


def get_button(key: str, lang: str = 'en') -> str:
    return BUTTONS.get(key, {}).get(lang, BUTTONS.get(key, {}).get('en', ''))



def format_credits(amount: int) -> str:
    return f'{amount} credit{"s" if amount != 1 else ""}'


def escape_markdown(text: str) -> str:
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text
