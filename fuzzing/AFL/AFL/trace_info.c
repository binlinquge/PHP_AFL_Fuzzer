#include <stdio.h>
#include <string.h>
#include <stdlib.h>

typedef long long int64;

int readTraceFile(int64 *result)
{
  FILE *f;
  int index1=0, index2=0;
  char one_num[21];
  char t;

  f = fopen("trace_info","r");
  t = fgetc(f);
  while(t!=EOF)
  {
    if (t==',')
    {
      one_num[index1]='\0';
      result[index2] = strtoll(one_num, NULL, 10);
      //printf("%lld\n", result[index2]);
      index1=0;
      index2+=1;
    }else{
      one_num[index1]=t;
      index1+=1;
    }
    t=fgetc(f);
  }

  fclose(f);
  return index2;
}

int traceToInt(char* trace, int64 *result)
{
  char t;
  int index1=0, index2=0, i=0;
  char one_num[21];

  for (i=0; i<strlen(trace); i++)
  {
    t = trace[i];
    if (t==',')
    {
      one_num[index1]='\0';
      result[index2] = strtoll(one_num, NULL, 10);
      index1=0;
      index2+=1;
    }else{
      one_num[index1]=t;
      index1+=1;
    }
  }

return index2;
}

/*
//used to test function readTraceFile()
int main()
{
  int i=0;
  int64 *result;
  result = (int64*)malloc(sizeof(int64) * 17261);
  readTraceFile(result);

  while (result[i]!=0)
  {
    printf("%lld,", result[i]);
    i++;
  }

  free(result);
  result=NULL;
return 0;
}
*/
/*
//used to test function traceToInt()
int main()
{
  char trace[]="416981194899478,416981194899479,416981194899486,1113762329264146,1113762329264149,1113762329264152,1113762329264153,1113762329264154,416981194899495,416981194899502,416981194899505,1110313470525453,1110313470525457,1110313470525462,1110313470525463,236098647228454,236098647228502,236098647228534,236098647228469,1110313470525569,1110313470525485,1110313470525489,1110313470525539,236098647228459,236098647228465,416981194899526,416981194899538,416981194899563,1117589145124877,1117589145124921,1117589145124993,1117589145124994,1117589145125016,1117589145125017,416981194899583,416981194899587,1117589145124996,416981194899591,416981194899592,416981194899604,1080768390497193,1080768390497200,1080768390497203,416981194899619,416981194899622,1117589145124924,";
  int i=0;

  int64 *result;
  result = (int64*)malloc(sizeof(int64) * 17261);
  traceToInt(trace, result);
 
  while (result[i]!=0)
  {
    printf("%lld\n", result[i]);
    i++;
  }

  free(result);
  result=NULL;
}
*/
