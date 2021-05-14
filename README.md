Steps to fuzz an PHP application:

a. Have the static analysis models in hand. (change the directory of the model files in line730 of nextToFuzz.py)

b. Have the static analysis satpath in hand. (change the directory of the satpath file in line854 of nextToFuzz.py)

c. Instrument the target application
  1. Assume the name of the appication is schoolmate
  2. Install the application properly. Make sure it can be reached from web server.
  3. Copy the whole application to /PROJECT_ROOT/PHP_Fuzzer
  4. Run the following command to instrument the target application
      python3 instrument.py ./schoolmate
  5. A new folder named schoolmate_ins will be created in the same folder
  6. Move the new folder to /var/www/html and rename it to schoolmate
  
d. Create the database which saves the trace infomation
  1. Modify the DB info of your own in the file /PROJECT_ROOT/AFL/AFL/create_database.py
  2. Run the file in step a to create the table which saves the trace infomation

e. Start fuzzing
  1. compile AFL
    in directory /PROJECT_ROOT/AFL/AFL do:
    make install
  2. Use the script /PROJECT_ROOT/AFL/AFL/nextToFuzz.py as the entry point to start fuzzing
    python3 nextToFuzz.py
  3. Do the fuzzing process according to the logs
  
Errors you might see:

a. AFL fuzzer failer related to the core.
  run the script /PROJECT_ROOT/AFL/AFL/modifyCore.sh to pass

File explaination:
  1. test_log_*: file names start with test_log_ is files that used for testing
  2. http.c and http.h contains the HTTP methods in C
  3. mutation.c contains the customized mutation methods
  4. afl-fuzz.c is the file that mostly modified in original AFL
