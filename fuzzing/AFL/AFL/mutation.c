#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <sys/time.h>
#include "cJSON.h"
#include <string.h>

/* string mutation function */
/*
  Input:
    input_json: json format of fuzzer input
    index: the index of parameter that need to be fuzzed
    pos: the position of character that need to be mutated
    result: string format of the mutated json input
*/
char* stringMutation(cJSON *input_json, int index , int pos, char* result){

  struct timeval start, end;
  gettimeofday(&start, NULL);
  srand(start.tv_usec);
  int temp = abs(rand()%57);
  //FILE *f;

  char* input=NULL;
  int i;
  //printf("mutating\n%d\n", index);

  input = cJSON_GetArrayItem(cJSON_GetArrayItem(input_json, index),0)->valuestring;
  char* input_cp = (char*)malloc(strlen(input)+1);
  strcpy(input_cp, input);
  //printf("%s\n", input);
  input[pos]=temp+65;
  //printf("%d\n", input[pos]);
  //printf("%d\n", temp);
  if (input[pos]>122){
    input[pos] = 65 + (input[pos] % 57);
    //printf("%c\n",input[pos]);
  }
  if (input[pos]>90 && input[pos]<97){
    input[pos] += 7;
    //printf("%c\n",input[pos]);
  }
  /*
  i=0;
  result[0]='\0';
  for (i=0; i<cJSON_GetArraySize(input_json); i++){
    //printf("%s\n",cJSON_Print(cJSON_GetArrayItem(input_json, i)));
    strcat(result,cJSON_GetArrayItem(input_json, i)->string);
    strcat(result,"=");
    strcat(result,cJSON_GetArrayItem(cJSON_GetArrayItem(input_json, i),0)->valuestring);
    strcat(result,"&");
    //printf("%s\n", result);
  }
  */
  strcpy(result, cJSON_Print(input_json));

  //f=fopen("test_log_mutation", "a");
  //fprintf(f, "%s\n", result);
  //fclose(f);

  strcpy(input, input_cp);
  free(input_cp);
  input_cp = NULL;
//strcpy(result,input_cp)
return result;
}


/* string mutation based on regular expression */
/*
  Input:
    input_json: json format of fuzzer input
    index: the index of parameter that need to be fuzzed
    pos: the position of character that need to be mutated
    result: string format of the mutated json input
*/
char* regexMutation(cJSON *input_json, int index , char* result, char* patten){

  char* input=NULL;
  int i;
  //printf("mutating\n%d\n", index);

  input = cJSON_GetArrayItem(cJSON_GetArrayItem(input_json, index),0)->valuestring;

  //char* input_cp = (char*)malloc(strlen(input)+1);
  //strcpy(input_cp, input);

  char cmd[200];
  cmd[0] = '\0';
  char result2[200];
  strcat(cmd, "python3 generateNewInput.py ");
  strcat(cmd, patten);
  //strcpy(result, system(cmd));
  //printf("%s\n", cmd);

  FILE *fp;
  char temp;
  fp = popen(cmd, "r");
  if (fp == NULL){
    printf("Fail to run command\n");
    return "Fail";
  }

  fgets(result2, 200, fp);
  result2[strlen(result2)-1]='\0';
  cJSON_GetArrayItem(cJSON_GetArrayItem(input_json, index),0)->valuestring = result2;

  pclose(fp);
  strcpy(result, cJSON_Print(input_json));

  cJSON_GetArrayItem(cJSON_GetArrayItem(input_json, index),0)->valuestring = input;

return result;
}

/*
//main function to test regexMutation
int main(){
  FILE *f;
  cJSON *input_js;
  char *result=(char*)malloc(500);
  char input[500];

  f = fopen("./input/test1.txt","r");
  fgets(input, 500, f);
  fclose(f);

  printf("%s\n", input);
  input_js = cJSON_Parse(input);
  printf("arrived here");
  regexMutation(input_js, 0, result, "[A-Z0-9._%+-]+@[A-Z0-9.-]+\\.[A-Z]{2,4}");
  printf("%s\n", result);
return 0;
}
*/

/*
  Input:
    input_json: json format of fuzzer input
    index: the index of parameter that need to be fuzzed
    result: string format of the mutated json input
*/
char* intMutation(cJSON *input_json, int index, char* result){
  struct timeval start, end;
  gettimeofday(&start, NULL);
  srand(start.tv_usec);
  int temp = rand();
  char* input=NULL;
  int i;
  input = cJSON_GetArrayItem(cJSON_GetArrayItem(input_json, index),0)->valuestring;
  //printf("%s", input);

  char* input_cp = (char*)malloc(strlen(input)+1);
  char* in_temp = (char*)malloc(21);
  //int input_cp;
  //input_cp = input;
  strcpy(input_cp, input);
  temp = temp % (int)pow(10, strlen(input));
  //input=temp;
printf("%d", temp);
  sprintf(in_temp, "%d", temp);
  strcpy(input, in_temp);
  //cJSON_GetArrayItem(cJSON_GetArrayItem(input_json, index),0)->valuestring = in_temp;
  strcpy(result, cJSON_Print(input_json));
  //input = input_cp;
  strcpy(input, input_cp);
  //cJSON_GetArrayItem(cJSON_GetArrayItem(input_json, index),0)->valuestring = input;
printf("%s\n", cJSON_Print(input_json));
  free(in_temp);
  in_temp = NULL;
  free(input_cp);
  input_cp = NULL;

return result;
}

/*
  Input:
    input_json: json format of fuzzer input
    index: the index of parameter that need to be fuzzed
    result: string format of the mutated json input
*/
char* boolMutation(cJSON *input_json, int index, char* result){
  char* input=NULL;
  cJSON *oj = cJSON_GetArrayItem(cJSON_GetArrayItem(input_json, index),0);
  input = cJSON_GetArrayItem(cJSON_GetArrayItem(input_json, index),0)->valuestring;

  char ju[6];
  if (strcmp(input,"false")==0)
  {
    strcpy(ju,"true");
  }else{
    strcpy(ju,"false");
  }

  //printf("%s", ju);
  oj->valuestring = ju;

  strcpy(result, cJSON_Print(input_json));

  oj->valuestring = input;

printf("%s\n", cJSON_Print(input_json));
return result;
}

char* regexMutation_old(char* patten, char* result){
  char cmd[200];
  cmd[0] = '\0';
  //char result[200];
  strcat(cmd, "python3 generateNewInput.py ");
  strcat(cmd, patten);
  //strcpy(result, system(cmd));
  printf("%s\n", cmd);

  FILE *fp;
  int index=0;
  char temp;
  fp = popen(cmd, "r");
  if (fp == NULL){
    printf("Fail to run command\n");
  }

  fgets(result, 200, fp);

//    result[index] = temp;
//    index+=1;
//    printf("%d\n", temp);
//  }
  pclose(fp);
//  result[index]='\0';
  return result;
}

/* string mutation function */
int stringMutation_original(char* input, int pos){

  struct timeval start, end;
  gettimeofday(&start, NULL);
  srand(start.tv_usec);
  int temp = abs(rand()%57);
  input[pos]=temp+65;
  //printf("%d\n", input[pos]);
  //printf("%d\n", temp);
  if (input[pos]>122){
    input[pos] = 65 + (input[pos] % 57);
    //printf("%c\n",input[pos]);
  }
  if (input[pos]>90 && input[pos]<97){
    input[pos] += 7;
    //printf("%c\n",input[pos]);
  }
return 0;
}
/*
//main function to test regexMutation_old
int main(){
  char result[200];
  regexMutation("[A-Z0-9._%+-]+@[A-Z0-9.-]+\\.[A-Z]{2,4}", result);
  printf("Result:%s\n", result);

return 0;
}
*/
/*
//main function to test stringMutation
int main(){
  FILE *f;
  cJSON *input_js;
  char *result=(char*)malloc(500);
  char input[500];

  f = fopen("./input/test1.txt","r");
  fgets(input, 500, f);
  fclose(f);

  printf("%s\n", input);
  input_js = cJSON_Parse(input);
  printf("arrived here");
  stringMutation(input_js, 3, 0,result);
  printf("%s\n", result);
return 0;
}
*/

/*
//main function to test
int main(){
  FILE *f;
  cJSON *input_js;
  char *result=(char*)malloc(200);
  char input[200];

  f = fopen("./input/test1.txt","r");
  fgets(input, 200, f);
  fclose(f);

  input_js = cJSON_Parse(input);
  boolMutation(input_js, 3, result);
  printf("%s\n", result);
return 0;
}
*/
