import json
import os
from typing import Any, Text, Dict, List, Optional

from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, ActiveLoop
from rasa_sdk.types import DomainDict

def load_json_data(file_name: Text) -> Optional[Dict]:
    """
    Loads data from a JSON file located in the 'data/knowledge_bases' directory.
    Returns None if the file is not found or is invalid.
    """
    base_dir = os.path.dirname(os.path.dirname(__file__))
    file_path = os.path.join(base_dir, 'data', 'knowledge_bases', file_name)
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading {file_name}: {e}")
        return None

CITY_TO_COUNTRY_MAP = load_json_data("city_to_country_mapping.json")
COUNTRY_INFO_DB = load_json_data("country_info.json")
BUDGET_DATA_DB = load_json_data("budget_data.json")
CHECKLISTS_DB = load_json_data("practical_checklists.json")
UNIVERSITIES_DB = load_json_data("universities_db.json")
COURSES_DB = load_json_data("courses_db.json")


def get_current_or_inferred_country(tracker: Tracker, dispatcher: CollectingDispatcher) -> Optional[Text]:
    """
    Determines the effective country, prioritizing current turn's entities.
    Handles invalid entities to prevent using stale slot data.
    """
    latest_message = tracker.latest_message
    country_entity = next(tracker.get_latest_entity_values("country"), None)
    city_entity = next(tracker.get_latest_entity_values("city"), None)

    entities_in_turn = [e['entity'] for e in latest_message.get('entities', [])]
    location_mentioned = "country" in entities_in_turn or "city" in entities_in_turn

    if country_entity:
        return country_entity

    if city_entity and CITY_TO_COUNTRY_MAP:
        mapped_country = CITY_TO_COUNTRY_MAP.get(city_entity.lower())
        if mapped_country:
            dispatcher.utter_message(f"Okay, I'll find info for {mapped_country.title()} (based on {city_entity.title()}).")
            return mapped_country

    if location_mentioned:
        return None

    existing_country_slot = tracker.get_slot("country")
    if existing_country_slot:
        return existing_country_slot

    return None

class ActionClearSlots(Action):
    def name(self) -> Text:
        return "action_clear_slots"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        return [
            SlotSet("country", None),
            SlotSet("city", None),
            SlotSet("program_type", None),
            SlotSet("field_of_study", None),
            SlotSet("budget_range", None),
            SlotSet("academic_level", None),
            SlotSet("duration", None),
            SlotSet("current_topic", None)
        ]

class ActionGetCountryInfo(Action):
    def name(self) -> Text:
        return "action_get_country_info"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        country = get_current_or_inferred_country(tracker, dispatcher)

        if COUNTRY_INFO_DB is None:
            dispatcher.utter_message(response="utter_database_error")
            return []

        if not country:
            dispatcher.utter_message(response="utter_ask_country")
            return [SlotSet("country", None), SlotSet("city", None)]

        country_key = country.lower()
        if country_key in COUNTRY_INFO_DB:
            info = COUNTRY_INFO_DB[country_key]
            uni_list_str = ', '.join(info.get('popular_universities', [])) or 'N/A'

            message = f"""
🌍 **{info.get('name', country.title())}** 🌍

📍 **Capital:** {info.get('capital', 'N/A')}
🗣️ **Language:** {info.get('language', 'N/A')}
💰 **Currency:** {info.get('currency', 'N/A')}
💵 **Cost of Living:** {info.get('cost_of_living', 'N/A')}
🌤️ **Climate:** {info.get('climate', 'N/A')}

🎓 **Popular Universities:**
{uni_list_str}

🎨 **Cultural Highlights:**
{info.get('cultural_highlights', 'N/A')}

📚 **Erasmus Info:**
{info.get('erasmus_info', 'N/A')}
            """
            dispatcher.utter_message(text=message)
            dispatcher.utter_message(f"Many students interested in {country.title()} also ask about visa requirements. Would you like me to tell you about that?")
            return [SlotSet("country", country), SlotSet("city", None), SlotSet("current_topic", "country_info")]
        else:
            dispatcher.utter_message(text=f"I don't have detailed information about {country.title()} yet.")
            return [SlotSet("country", None), SlotSet("city", None)]


class ActionBudgetCalculator(Action):
    def name(self) -> Text:
        return "action_budget_calculator"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        country = get_current_or_inferred_country(tracker, dispatcher)

        if BUDGET_DATA_DB is None:
            dispatcher.utter_message(response="utter_database_error")
            return []

        if not country:
            dispatcher.utter_message(response="utter_ask_country")
            return [SlotSet("country", None), SlotSet("city", None)]

        country_key = country.lower()
        if country_key in BUDGET_DATA_DB:
            data = BUDGET_DATA_DB[country_key]
            try:
                duration = tracker.get_slot("duration")
                months = int(''.join(filter(str.isdigit, duration))) if duration else 5
            except (ValueError, TypeError):
                months = 5

            message = f"""
💰 **Budget Estimate for {country.title()}** (per month)

📊 **Monthly Costs:**
• Budget option: €{data.get('low', 0)}
• Comfortable: €{data.get('medium', 0)}
• Premium: €{data.get('high', 0)}

📅 **For {months} months (estimated):**
• Budget total: €{data.get('low', 0) * months}
• Comfortable total: €{data.get('medium', 0) * months}
• Premium total: €{data.get('high', 0) * months}

💡 **Note:** The Erasmus+ grant (typically €300-500/month) will help cover a significant portion of these costs!
            """
            dispatcher.utter_message(text=message)
            return [SlotSet("country", country), SlotSet("city", None), SlotSet("current_topic", "finances")]
        else:
            dispatcher.utter_message(text=f"I'm sorry, I don't have specific budget data for {country.title()} yet.")
            return [SlotSet("country", None), SlotSet("city", None)]


class ActionPracticalChecklist(Action):
    def name(self) -> Text:
        return "action_practical_checklist"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        country = get_current_or_inferred_country(tracker, dispatcher)

        if CHECKLISTS_DB is None:
            dispatcher.utter_message(response="utter_database_error")
            return []

        general_checklist = CHECKLISTS_DB.get("general", [])
        country_specific_checklists = CHECKLISTS_DB.get("country_specific", {})

        message = "📋 **Pre-Departure Checklist:**\n\n"
        message += "\n".join(f"• {item}" for item in general_checklist)

        if country and country.lower() in country_specific_checklists:
            message += f"\n\n🎯 **Specific for {country.title()}:**\n"
            message += "\n".join(f"• {item}" for item in country_specific_checklists[country.lower()])
        elif country:
            message += f"\n\nI don't have a specific checklist for {country.title()}, but the general tips should be very helpful!"

        message += "\n\n💡 Start preparations 3-6 months before departure!"

        dispatcher.utter_message(text=message)
        return [SlotSet("country", country), SlotSet("city", None), SlotSet("current_topic", "practical")]



class ActionGetErasmusOverviewAndReset(Action):
    def name(self) -> Text:
        return "action_get_erasmus_overview_and_reset"
    def run(self, d: CollectingDispatcher, t: Tracker, dom: Dict) -> List[Dict[Text, Any]]:
        d.utter_message(response="utter_erasmus_overview")
        return []

class ActionGetHousingInfo(Action):
    def name(self) -> Text:
        return "action_get_housing_info"
    def run(self, d: CollectingDispatcher, t: Tracker, dom: Dict) -> List[Dict[Text, Any]]:
        d.utter_message(response="utter_housing_info")
        return [SlotSet("current_topic", "housing")]

class ActionGetVisaInfo(Action):
    def name(self) -> Text:
        return "action_get_visa_info"
    def run(self, d: CollectingDispatcher, t: Tracker, dom: Dict) -> List[Dict[Text, Any]]:
        d.utter_message(response="utter_visa_requirements")
        return [SlotSet("current_topic", "visa")]

class ActionGetLanguageInfo(Action):
    def name(self) -> Text:
        return "action_get_language_info"
    def run(self, d: CollectingDispatcher, t: Tracker, dom: Dict) -> List[Dict[Text, Any]]:
        d.utter_message(response="utter_language_requirements")
        return [SlotSet("current_topic", "language")]

class ActionGetDurationInfo(Action):
    def name(self) -> Text:
        return "action_get_duration_info"
    def run(self, d: CollectingDispatcher, t: Tracker, dom: Dict) -> List[Dict[Text, Any]]:
        d.utter_message(response="utter_duration_options")
        return [SlotSet("current_topic", "duration")]

class ActionGetAcademicsInfo(Action):
    def name(self) -> Text:
        return "action_get_academics_info"
    def run(self, d: CollectingDispatcher, t: Tracker, dom: Dict) -> List[Dict[Text, Any]]:
        d.utter_message(response="utter_academics")
        return [SlotSet("current_topic", "academics")]


class ActionHandleContextualQuestion(Action):
    def name(self) -> Text:
        return "action_handle_contextual_question"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        topic = tracker.get_slot("current_topic")

        if topic == "finances":
            return ActionBudgetCalculator().run(dispatcher, tracker, domain)
        elif topic == "practical":
            return ActionPracticalChecklist().run(dispatcher, tracker, domain)
        elif topic == "country_info":
            return ActionGetCountryInfo().run(dispatcher, tracker, domain)
        elif topic in ["housing", "visa", "language", "duration", "academics"]:
            country = get_current_or_inferred_country(tracker, dispatcher)
            response = f"utter_{topic}_info" if topic == "housing" else f"utter_{topic}_requirements" if topic == "visa" or topic == "language" else f"utter_{topic}_options" if topic == "duration" else f"utter_{topic}"
            dispatcher.utter_message(response=response)
            if country:
                 dispatcher.utter_message(text=f"This is the general information. It might vary for {country.title()}.")
            return [SlotSet("country", country), SlotSet("current_topic", topic)]
        else:
            dispatcher.utter_message(text="I'm not sure what topic we were on. Could you please ask your question again more specifically?")
            return [SlotSet("current_topic", None)]


class ValidateUniversitySearchForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_university_search_form"

    async def validate_country(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict) -> Dict[Text, Any]:
        """Validate `country` value. Checks against the knowledge base."""
        if not slot_value:
            dispatcher.utter_message(text="I didn't quite catch the country. Could you please specify a country participating in Erasmus+?")
            return {"country": None}
        if COUNTRY_INFO_DB and slot_value.lower() in COUNTRY_INFO_DB:
            return {"country": slot_value}
        else:
            dispatcher.utter_message(text=f"I don't have detailed information for '{slot_value}'. Please provide a recognized Erasmus+ country.")
            return {"country": None}

    async def validate_field_of_study(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict) -> Dict[Text, Any]:
        """Validate `field_of_study` value."""
        if slot_value:
            return {"field_of_study": slot_value}
        else:
            dispatcher.utter_message(text="I didn't quite catch the field of study. What area are you interested in?")
            return {"field_of_study": None}


class ActionFindCoursesAndUniversities(Action):
    def name(self) -> Text:
        return "action_find_courses_and_universities"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        country = tracker.get_slot("country")
        field_of_study = tracker.get_slot("field_of_study")

        if UNIVERSITIES_DB is None or COURSES_DB is None:
            dispatcher.utter_message(response="utter_database_error")
            return []

        if not country or not field_of_study:
            dispatcher.utter_message(text="I need both a country and a field of study to find recommendations.")
            return [SlotSet("country", None), SlotSet("field_of_study", None), SlotSet("city", None), SlotSet("current_topic", None)]

        country_key = country.lower()
        field_key = field_of_study.lower()

        country_uni_data = UNIVERSITIES_DB.get(country_key, {})
        unis = country_uni_data.get(field_key)

        field_course_data = COURSES_DB.get(field_key, {})
        courses = field_course_data.get(country_key)

        message = ""
        found_data = False

        if unis:
            message += f"🎓 **Top Universities for {field_of_study.title()} in {country.title()}:**\n" + "\n".join([f"• {uni}" for uni in unis]) + "\n\n"
            found_data = True
        
        if courses:
            if not found_data:
                message += f"📚 **Recommended Programs for {field_of_study.title()} in {country.title()}:**\n"
            else:
                message += f"📚 **Also, Recommended Programs:**\n"
            message += "\n".join([f"• {course}" for course in courses]) + "\n\n"
            found_data = True

        if not found_data:
            dispatcher.utter_message(text=f"I don't have specific university or course recommendations for **{field_of_study.title()}** in **{country.title()}**.")
            dispatcher.utter_message(text=f"Would you like to try a different field of study, or perhaps I can tell you more about general information for studying in {country.title()}?")
        else:
            dispatcher.utter_message(text=message)


        return [SlotSet("country", None), SlotSet("field_of_study", None), SlotSet("city", None), SlotSet("current_topic", None)]
 
class ActionRestartConversation(Action):
    """Resets the conversation by clearing all relevant slots."""
    def name(self) -> Text:
        return "action_restart_conversation"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        return [
            SlotSet("country", None),
            SlotSet("city", None),
            SlotSet("program_type", None),
            SlotSet("field_of_study", None),
            SlotSet("budget_range", None),
            SlotSet("academic_level", None),
            SlotSet("duration", None),
            SlotSet("current_topic", None)
        ]

class ActionCancelFormAndClearSlots(Action):
    """Deactivates the form and clears form-specific slots."""
    def name(self) -> Text:
        return "action_cancel_form_and_clear_slots"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        return [
            SlotSet("country", None),
            SlotSet("city", None),
            SlotSet("field_of_study", None),
            SlotSet("academic_level", None),
            ActiveLoop(None) 
        ]

