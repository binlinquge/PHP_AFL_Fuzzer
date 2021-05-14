Steps to fuzz an PHP application:
1. Have the static analysis models in hand. (change the directory of the model files in line730 of nextToFuzz.py)
2. Have the static analysis satpath in hand. (change the directory of the satpath file in line854 of nextToFuzz.py)
3. Instrument the target application:
  a. Assume the name of the appication is schoolmate
  b. Install the application properly. Make sure it can be reached from web server.
  b. Copy the whole application to /PROJECT_ROOT/PHP_Fuzzer
  c. Run the following command to instrument the target application
      python3 instrument.py ./schoolmate
  d. A new folder named schoolmate_ins will be created in the same folder
  e. Move the new folder to /var/www/html and rename it to schoolmate
4. Create the database which saves the trace infomation
  a. Modify the DB info of your own in the file /PROJECT_ROOT/AFL/AFL/create_database.py
  b. Run the file in step a to create the table which saves the trace infomation
5. Start fuzzing
  a. compile AFL
    in directory /PROJECT_ROOT/AFL/AFL do:
    make install
  b. Use the script /PROJECT_ROOT/AFL/AFL/nextToFuzz.py as the entry point to start fuzzing
    python3 nextToFuzz.py
  c. Do the fuzzing process according to the logs
  
Errors you might see:
1. AFL fuzzer failer related to the core.
  run the script /PROJECT_ROOT/AFL/AFL/modifyCore.sh to pass

File explaination:
  1. test_log_*: file names start with test_log_ is files that used for testing
  2. http.c and http.h contains the HTTP methods in C
  3. mutation.c contains the customized mutation methods
  4. afl-fuzz.c is the file that mostly modified in original AFL
