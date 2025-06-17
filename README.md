**Erasmus Information Assistant (**`Erasmus Buddy`**)**
This repository contains the source code for the "Erasmus Buddy," a conversational AI built with Rasa. This chatbot is designed to assist prospective students with their questions about the Erasmus+ exchange program, covering topics from eligibility and application procedures to detailed information about countries, finances, and university recommendations.
**Prerequisites**
Before you begin, ensure you have the following installed on your system:
* **Python** (version 3.8, 3.9, or 3.10)
* **pip** (Python package installer)
* **Git** (for cloning the repository)
**Installation & Setup**
Follow these steps to set up the project locally in a clean Python virtual environment.
**1. Clone the Repository**
First, clone this repository to your local machine using Git:

```
git clone https://github.com/Michael-Gkotsis/rasa-erasmus-bot.git
cd [REPOSITORY_FOLDER_NAME]


```

**2. Create and Activate a Virtual Environment**
It is highly recommended to use a virtual environment to manage dependencies and avoid conflicts with other Python projects.
**On macOS / Linux:**

```
python3 -m venv venv
chmod +x venv/bin/activate # if not allowed to execute
source venv/bin/activate


```

**On Windows:**

```
python -m venv venv
.\venv\Scripts\activate


```

After activation, you will see `(venv)` at the beginning of your command prompt, indicating that the virtual environment is active.
**3. Install Dependencies**
Now, install all the required Python packages using pip:

```
pip install rasa


```

This command will download and install Rasa, TensorFlow, and the sentence-transformers library needed for the language model defined in `config.yml`.
**Usage**
To interact with your chatbot, you need to run two separate processes: the **Rasa action server** and the **Rasa shell**.
**1. Train the Rasa Model**
Before you can run the bot, you need to train the NLU and dialogue models. This will create a bundled model file in the `models/` directory.

```
rasa train


```

**2. Run the Action Server**
The action server is a separate process that runs your custom Python code from `actions.py` (e.g., querying the knowledge bases).
Open a **new terminal** in the same project directory, activate the virtual environment (`source venv/bin/activate`), and run:

```
rasa run actions


```

Keep this terminal running.
**3. Run the Chatbot Shell**
Go back to your **first terminal** (where you trained the model) and start the interactive shell to talk to your chatbot:

```
rasa shell


```

You can now start interacting with your "Erasmus Buddy"! To stop the bot, you can type `/stop` in the shell or press `Ctrl + C`.
**Project Structure**
Here is a brief overview of the key files and directories in this project:
* `actions/actions.py`: Contains the custom Python code for actions that query the knowledge bases, validate forms, and perform other complex logic.
* `data/`: This directory holds all the NLU training data, stories, and rules. The `.yml` files within define the bot's conversational abilities.
* `data/knowledge_bases/`: Contains the `.json` files that act as the bot's external knowledge source for countries, universities, budgets, etc.
* `config.yml`: Defines the NLU processing pipeline and the policies for dialogue management.
* `domain.yml`: The bot's "world." It lists all intents, entities, slots, responses, and actions the bot knows about.
* `models/`: The trained model files are stored here after running `rasa train`.
