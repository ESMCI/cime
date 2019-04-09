/*
** Fortran wrappers for timing library routines
*/

#include <string.h>
#include <stdlib.h>
#include "private.h" /* MAX_CHARS, bool */
#include "gptl.h"    /* function prototypes and HAVE_MPI logic*/

#if ( defined FORTRANCAPS )

#define gptlevent_name_to_code GPTLEVENT_NAME_TO_CODE
#define gptlevent_code_to_name GPTLEVENT_CODE_TO_NAME

#elif ( defined INCLUDE_CMAKE_FCI )

#define gptlevent_name_to_code      FCI_GLOBAL(gptlevent_name_to_code,GPTLEVENT_NAME_TO_CODE)
#define gptlevent_code_to_name      FCI_GLOBAL(gptlevent_code_to_name,GPTLEVENT_CODE_TO_NAME)
#elif ( defined FORTRANUNDERSCORE )

#define gptlevent_name_to_code gptlevent_name_to_code_
#define gptlevent_code_to_name gptlevent_code_to_name_

#elif ( defined FORTRANDOUBLEUNDERSCORE )

#define gptlevent_name_to_code gptlevent_name_to_code__
#define gptlevent_code_to_name gptlevent_code_to_name__

#endif

/*
** Local function prototypes
*/

#ifdef HAVE_PAPI
/* int gptl_papilibraryinit (void); */
int gptlevent_name_to_code (const char *str, int *code, int nc);
int gptlevent_code_to_name (int *code, char *str, int nc);
#endif

/*
** Fortran wrapper functions start here
*/

int gptlinitialize (void)
{
  return GPTLinitialize ();
}

int gptlfinalize (void)
{
  return GPTLfinalize ();
}

int gptlpr_set_append (void)
{
  return GPTLpr_set_append ();
}

int gptlpr_query_append (void)
{
  return GPTLpr_set_append ();
}

int gptlpr_set_write (void)
{
  return GPTLpr_set_append ();
}

int gptlpr_query_write (void)
{
  return GPTLpr_set_append ();
}

int gptlpr (int *procid)
{
  return GPTLpr (*procid);
}

int gptlpr_file (char *file, int nc1)
{
  char *locfile;
  int ret;

  if ( ! (locfile = (char *) malloc (nc1+1)))
    return GPTLerror ("gptlpr_file: malloc error\n");

  snprintf (locfile, nc1+1, "%s", file);

  ret = GPTLpr_file (locfile);
  free (locfile);
  return ret;
}

int gptlpr_summary (int *fcomm)
{
#ifdef HAVE_MPI
  MPI_Comm ccomm;
#ifdef HAVE_COMM_F2C
  ccomm = MPI_Comm_f2c (*fcomm);
#else
  /* Punt and try just casting the Fortran communicator */
  ccomm = (MPI_Comm) *fcomm;
#endif
#else
  int ccomm = 0;
#endif 

  return GPTLpr_summary (ccomm);
}

int gptlpr_summary_file (int *fcomm, char *file, int nc1)
{
  char *locfile;
  int ret;

#ifdef HAVE_MPI
  MPI_Comm ccomm;
#ifdef HAVE_COMM_F2C
  ccomm = MPI_Comm_f2c (*fcomm);
#else
  /* Punt and try just casting the Fortran communicator */
  ccomm = (MPI_Comm) *fcomm;
#endif
#else
  int ccomm = 0;
#endif 

  if ( ! (locfile = (char *) malloc (nc1+1)))
    return GPTLerror ("gptlpr_summary_file: malloc error\n");

  snprintf (locfile, nc1+1, "%s", file);

  ret = GPTLpr_summary_file (ccomm, locfile);
  free (locfile);
  return ret;
}

int gptlbarrier (int *fcomm, char *name, int nc1)
{
  char cname[MAX_CHARS+1];
  int numchars;
#ifdef HAVE_MPI
  MPI_Comm ccomm;
#ifdef HAVE_COMM_F2C
  ccomm = MPI_Comm_f2c (*fcomm);
#else
  /* Punt and try just casting the Fortran communicator */
  ccomm = (MPI_Comm) *fcomm;
#endif
#else
  int ccomm = 0;
#endif 

  numchars = MIN (nc1, MAX_CHARS);
  strncpy (cname, name, numchars);
  cname[numchars] = '\0';
  return GPTLbarrier (ccomm, cname);
}

int gptlreset (void)
{
  return GPTLreset();
}

int gptlstamp (double *wall, double *usr, double *sys)
{
  return GPTLstamp (wall, usr, sys);
}

int gptlstart (char *name, int nc1)
{
  char cname[MAX_CHARS+1];
  int numchars;

  numchars = MIN (nc1, MAX_CHARS);
  strncpy (cname, name, numchars);
  cname[numchars] = '\0';
  return GPTLstart (cname);
}

int gptlstart_handle (char *name, void **handle, int nc1)
{
  char cname[MAX_CHARS+1];
  int numchars;

  if (*handle) {
    cname[0] = '\0';
  } else {
    numchars = MIN (nc1, MAX_CHARS);
    strncpy (cname, name, numchars);
    cname[numchars] = '\0';
  }
  return GPTLstart_handle (cname, handle);
}

int gptlstop (char *name, int nc1)
{
  char cname[MAX_CHARS+1];
  int numchars;

  numchars = MIN (nc1, MAX_CHARS);
  strncpy (cname, name, numchars);
  cname[numchars] = '\0';
  return GPTLstop (cname);
}

int gptlstop_handle (char *name, void **handle, int nc1)
{
  char cname[MAX_CHARS+1];
  int numchars;

  if (*handle) {
    cname[0] = '\0';
  } else {
    numchars = MIN (nc1, MAX_CHARS);
    strncpy (cname, name, numchars);
    cname[numchars] = '\0';
  }
  return GPTLstop_handle (cname, handle);
}

int gptlsetoption (int *option, int *val)
{
  return GPTLsetoption (*option, *val);
}

int gptlenable (void)
{
  return GPTLenable ();
}

int gptldisable (void)
{
  return GPTLdisable ();
}

int gptlsetutr (int *option)
{
  return GPTLsetutr (*option);
}

int gptlquery (const char *name, int *t, int *count, int *onflg, double *wallclock, 
	       double *usr, double *sys, long long *papicounters_out, int *maxcounters, 
	       int nc)
{
  char cname[MAX_CHARS+1];
  int numchars;

  numchars = MIN (nc, MAX_CHARS);
  strncpy (cname, name, numchars);
  cname[numchars] = '\0';
  return GPTLquery (cname, *t, count, onflg, wallclock, usr, sys, papicounters_out, *maxcounters);
}

int gptlquerycounters (const char *name, int *t, long long *papicounters_out, int nc)
{
  char cname[MAX_CHARS+1];
  int numchars;

  numchars = MIN (nc, MAX_CHARS);
  strncpy (cname, name, numchars);
  cname[numchars] = '\0';
  return GPTLquerycounters (cname, *t, papicounters_out);
}

int gptlget_wallclock (const char *name, int *t, double *value, int nc)
{
  char cname[MAX_CHARS+1];
  int numchars;

  numchars = MIN (nc, MAX_CHARS);
  strncpy (cname, name, numchars);
  cname[numchars] = '\0';

  return GPTLget_wallclock (cname, *t, value);
}

int gptlget_eventvalue (const char *timername, const char *eventname, int *t, double *value, 
			int nc1, int nc2)
{
  char ctimername[MAX_CHARS+1];
  char ceventname[MAX_CHARS+1];
  int numchars;

  numchars = MIN (nc1, MAX_CHARS);
  strncpy (ctimername, timername, numchars);
  ctimername[numchars] = '\0';

  numchars = MIN (nc2, MAX_CHARS);
  strncpy (ceventname, eventname, numchars);
  ceventname[numchars] = '\0';

  return GPTLget_eventvalue (ctimername, ceventname, *t, value);
}

int gptlget_nregions (int *t, int *nregions)
{
  return GPTLget_nregions (*t, nregions);
}

int gptlget_regionname (int *t, int *region, char *name, int nc)
{
  int n;
  int ret;

  ret = GPTLget_regionname (*t, *region, name, nc);
  /* Turn nulls into spaces for fortran */
  for (n = 0; n < nc; ++n)
    if (name[n] == '\0')
      name[n] = ' ';
  return ret;
}

int gptlget_memusage (int *size, int *rss, int *share, int *text, int *datastack)
{
  return GPTLget_memusage (size, rss, share, text, datastack);
}

int gptlprint_memusage (const char *str, int nc)
{
  char cname[128+1];
  int numchars = MIN (nc, 128);

  strncpy (cname, str, numchars);
  cname[numchars] = '\0';
  return GPTLprint_memusage (cname);
}

#ifdef HAVE_PAPI
#include <papi.h>

int gptl_papilibraryinit (void)
{
  return GPTL_PAPIlibraryinit ();
}

int gptlevent_name_to_code (const char *str, int *code, int nc)
{
  char cname[PAPI_MAX_STR_LEN+1];
  int numchars = MIN (nc, PAPI_MAX_STR_LEN);

  strncpy (cname, str, numchars);
  cname[numchars] = '\0';

  /* "code" is an int* and is an output variable */

  return GPTLevent_name_to_code (cname, code);
}

int gptlevent_code_to_name (int *code, char *str, int nc)
{
  int i;

  if (nc < PAPI_MAX_STR_LEN)
    return GPTLerror ("gptl_event_code_to_name: output name must hold at least %d characters\n",
		      PAPI_MAX_STR_LEN);

  if (GPTLevent_code_to_name (*code, str) == 0) {
    for (i = strlen(str); i < nc; ++i)
      str[i] = ' ';
  } else {
    return GPTLerror ("");
  }
  return 0;
}
#else

int gptl_papilibraryinit (void)
{
  return GPTL_PAPIlibraryinit ();
}

int gptlevent_name_to_code (const char *str, int *code, int nc)
{
  return GPTLevent_name_to_code (str, code);
}

int gptlevent_code_to_name (const int *code, char *str, int nc)
{
  return GPTLevent_code_to_name (*code, str);
}

#endif
