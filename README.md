# CarrotBot
CarrotBot for Piazza

## Installing

    # Dependency for connecting to Piazza
    pip install piazza-api
    
    # Dependency for machine learning
    pip install numpy beautifulsoup4 nltk scikit-learn scipy
    
    https://github.com/CurtisFenner/CarrotBot.git
    
## Running

Edit `configuration.json` to list your course and any Piazza offerings (see repo for example).

    python main.py

Enter a username/password for a Piazza account enrolled in your Piazza course.

Visit http://localhost:8080/robot.html to turn on auto-answer robot.

Visit http://localhost:8080/?course=YOURCOURSENAMEHERE to see graphs for your Piazza courses.
