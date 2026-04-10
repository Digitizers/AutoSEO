"""
Seed apps4all static pages to MongoDB.
Extracts content from the hardcoded Next.js components and inserts as staticPage docs.
Run: python scripts/seed_apps4all_static_pages.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import yaml
from datetime import datetime, timezone
from pymongo import MongoClient

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.apps4all.yaml")

with open(CONFIG_PATH, encoding="utf-8") as f:
    config = yaml.safe_load(f)

client = MongoClient(config["mongodb"]["uri"], serverSelectionTimeoutMS=20000)
db = client[config["mongodb"]["database"]]
col = db[config["mongodb"]["collection"]]

def p(text):
    return {"type": "paragraph", "content": [{"type": "text", "text": text}]}

def h(level, text):
    return {"type": "heading", "attrs": {"level": level}, "content": [{"type": "text", "text": text}]}

def ul(items):
    return {
        "type": "bulletList",
        "content": [
            {"type": "listItem", "content": [p(item)]}
            for item in items
        ]
    }

now = datetime.now(timezone.utc)

pages = [
    {
        "pageId": "services",
        "type": "staticPage",
        "title": "שירותי פיתוח תוכנה | Apps4All",
        "content": {
            "type": "doc",
            "content": [
                h(1, "מה אנחנו בונים"),
                p("סוכני AI וכלי בינה מלאכותית, אפליקציות, אתרים ומערכות CRM – הכל מותאם אישית, מקצה לקצה."),

                h(2, "אפליקציות מובייל"),
                p("אפליקציות iOS ו-Android חווייתיות – מרעיון ראשוני ועד השקה בחנויות."),
                ul([
                    "פיתוח React Native עם ביצועים ו-UX מלוטש",
                    "Onboarding, תשלומים, Push Notifications ואבטחה מובנית",
                    "CI/CD ועדכונים מהירים ישירות למשתמשים",
                    "Analytics מלא ואופטימיזציה מתמשכת",
                ]),

                h(2, "אתרים ופורטלים"),
                p("אתרי SaaS, פורטלים ומערכות ניהול מודרניות עם Next.js."),
                ul([
                    "דירוג גבוה בגוגל – SEO וביצועים מעולים מובנים",
                    "אבטחה והרשאות: RBAC, חתימות דיגיטליות והצפנת נתונים",
                    "Scalability: ארכיטקטורה שגדלה איתכם מ-100 למאות אלפי משתמשים",
                    "רספונסיביות: חוויה מושלמת מ-Desktop, Tablet ועד Mobile",
                ]),

                h(2, "מערכות CRM"),
                p("CRM מותאם בדיוק לעסק – ניהול לקוחות, לידים ותהליכי מכירה במקום אחד."),
                ul([
                    "עיצוב ויישום CRM שמתאים לזרימות העסקיות שלכם",
                    "360° לקוח: פייפליין, שירות, חוזים ו-Billing במקום אחד",
                    "אוטומציות מכירה ושירות: התראות, SLA ו-Scoring חכם",
                    "דשבורדים בזמן אמת ומדדי הכנסות לפי ערוץ ומוצר",
                ]),

                h(2, "AI ואוטומציות"),
                p("סוכנים חכמים, אוטומציית תהליכים וניתוח נתונים שעובדים בשבילכם 24/7."),
                ul([
                    "בוטים חכמים: קביעת תורים, עדכון סטטוס הזמנה ושליפת נתונים",
                    "RAG: סוכן שקורא את הידע הארגוני שלכם ועונה בדיוק מוחלט",
                    "אוטומציית תהליכים: חיבור מערכות ליצירת זרימה עצמאית ללא מגע יד",
                    "Smart Insights: ניתוח נתונים, חיזוי נטישה ודירוג לידים חכם",
                ]),
            ],
        },
        "createdAt": now,
        "updatedAt": now,
    },
    {
        "pageId": "about",
        "type": "staticPage",
        "title": "אודות Apps4All | חברת פיתוח תוכנה מתל אביב",
        "content": {
            "type": "doc",
            "content": [
                h(1, "מרעיון למוצר – בארבעה שלבים"),
                p("תהליך ברור ושקוף שמוביל את המוצר שלכם מהרעיון הראשוני ועד לאוויר – ומעבר לזה."),

                h(2, "אפיון ותכנון"),
                p("נפגשים, מבינים את העסק שלכם ומתרגמים את הרעיון לתוכנית עבודה מדויקת עם לוחות זמנים ברורים."),

                h(2, "עיצוב ופיתוח"),
                p("מעצבים ממשק נוח ומפתחים קוד נקי וניתן להרחבה. אתם מעודכנים בכל שלב ורואים התקדמות בזמן אמת."),

                h(2, "בדיקות ואבטחת איכות"),
                p("לפני שיוצאים לאוויר – בדיקות קפדניות, תיקוני באגים ובדיקות עומסים. המטרה: שתהיו בטוחים ב-100%."),

                h(2, "השקה, תשתיות וליווי"),
                p("תשתיות ענן חזקות, השקה מבוקרת והדרכה לצוות. ליווי טכני שוטף ושיפורים מתמידים – אנחנו הגב שלכם."),

                h(2, "מי אנחנו"),
                p("Apps4All היא חברת פיתוח תוכנה מתל אביב המתמחה בבניית מערכות דיגיטליות מקצה לקצה. אנחנו בונים אפליקציות מובייל, מערכות CRM, פתרונות AI ואינטגרציות עסקיות לעסקים בישראל."),
                p("הטון שלנו: מקצועי, ישיר, טכנולוגי אבל נגיש. אנחנו מדברים בגובה העיניים ומתרגמים טכנולוגיה מורכבת לשפה עסקית ברורה."),
                ul([
                    "מערכת דיגיטלית מקצה לקצה — מובייל, ווב, CRM ואינטגרציות במקום אחד",
                    "פתרונות AI מתקדמים — סוכני AI, אוטומציות חכמות ודשבורדים מבוססי נתונים",
                    "טכנולוגיות מודרניות: React Native, Next.js, Node.js, Firebase",
                    "תמחור שקוף, ליווי צמוד ותמיכה שוטפת לאחר השקה",
                    "ניסיון מוכח עם אפליקציות בפרודקשן — ספורט, חינוך, מסחר אונליין",
                    "+50 פרויקטים שהושקו",
                ]),
            ],
        },
        "createdAt": now,
        "updatedAt": now,
    },
    {
        "pageId": "faq",
        "type": "staticPage",
        "title": "שאלות נפוצות על פיתוח אפליקציות | Apps4All",
        "content": {
            "type": "doc",
            "content": [
                h(1, "שאלות נפוצות"),
                p("תשובות לשאלות הנפוצות ביותר על פיתוח אפליקציות, עלויות ותהליך העבודה עם Apps4All."),

                h(2, "כמה עולה לפתח אפליקציה?"),
                p("עלות פיתוח אפליקציה תלויה בסוג, בפיצ'רים ובמורכבות. אפליקציה בסיסית מתחילה מ-30,000 ש\"ח, בעוד אפליקציות מורכבות עם CRM ו-AI יכולות להגיע ל-200,000 ש\"ח ומעלה. אנחנו מציעים הצעת מחיר מפורטת לאחר פגישת אפיון חינמית."),

                h(2, "כמה זמן לוקח לפתח אפליקציה?"),
                p("זמן הפיתוח משתנה: MVP בסיסי – 6-10 שבועות, אפליקציה מלאה – 3-6 חודשים, מערכת CRM מורכבת – 4-8 חודשים. נותנים לכם לוח זמנים מדויק לאחר פגישת האפיון."),

                h(2, "האם אתם עובדים עם עסקים קטנים?"),
                p("כן! אנחנו עובדים עם עסקים מכל הגדלים – מסטארטאפ בשלב ה-MVP ועד חברות גדולות הזקוקות לשדרוג מערכות קיימות. לכל לקוח אנחנו בונים פתרון מותאם לתקציב ולצרכים שלו."),

                h(2, "באילו טכנולוגיות אתם משתמשים?"),
                p("אנחנו עובדים עם React Native ו-Expo לאפליקציות מובייל, Next.js לאתרים ופורטלים, Node.js לבק-אנד, Firebase ו-MongoDB למסדי נתונים, ו-OpenAI/Claude לפתרונות AI."),

                h(2, "מה קורה אחרי ההשקה?"),
                p("אנחנו מציעים ליווי טכני שוטף לאחר השקה: תמיכה, עדכונים, תיקוני באגים והוספת פיצ'רים חדשים. לקוחות רבים עובדים איתנו שנים רבות לאחר השקת הפרויקט הראשון."),

                h(2, "האם אתם מפתחים גם לאנדרואיד וגם לiPhone?"),
                p("כן! אנחנו מפתחים עם React Native שמאפשר לנו לבנות אפליקציה אחת שרצה על iOS ו-Android גם יחד, מה שמקצר זמן ועלויות פיתוח משמעותית."),
            ],
        },
        "createdAt": now,
        "updatedAt": now,
    },
]

inserted = 0
skipped = 0
for page in pages:
    existing = col.find_one({"pageId": page["pageId"], "type": "staticPage"})
    if existing:
        print(f"  [skip] pageId='{page['pageId']}' already exists (_id: {existing['_id']})")
        skipped += 1
    else:
        result = col.insert_one(page)
        print(f"  [insert] pageId='{page['pageId']}' _id: {result.inserted_id}")
        inserted += 1

print(f"\nDone: {inserted} inserted, {skipped} skipped")
client.close()
