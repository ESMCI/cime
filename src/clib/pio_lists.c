#include <config.h>
#include <pio.h>
#include <pio_internal.h>
#include <string.h>
#include <stdio.h>

static io_desc_t *pio_iodesc_list=NULL;
static io_desc_t *current_iodesc=NULL;
static iosystem_desc_t *pio_iosystem_list=NULL;
static file_desc_t *pio_file_list = NULL;
static file_desc_t *current_file=NULL;

/** Add a new entry to the global list of open files.
 *
 * @param file pointer to the file_desc_t struct for the new file.
*/
void pio_add_to_file_list(file_desc_t *file)
{
  file_desc_t *cfile;

  /* This file will be at the end of the list, and have no next. */
  file->next = NULL;

  /* Get a pointer to the global list of files. */
  cfile = pio_file_list;

  /* Keep a global pointer to the current file. */
  current_file = file;

  /* If there is nothing in the list, then file will be the first
   * entry. Otherwise, move to end of the list. */
  if (!cfile)
      pio_file_list = file;
  else
  {
      while (cfile->next)
	  cfile = cfile->next;
      cfile->next = file;
  }
}

/** Given ncid, find the file_desc_t data for an open file. The ncid
 * used is the interally generated pio_ncid. */
file_desc_t *pio_get_file_from_id(int ncid)
{
    file_desc_t *cfile = NULL;

    /* Check to see if the current_file is already set to this ncid. */
    if (current_file && current_file->pio_ncid == ncid)
	cfile = current_file;
    else
	for (cfile = pio_file_list; cfile; cfile = cfile->next)
	    if (cfile->pio_ncid == ncid)
	    {
		current_file = cfile;
		break;
	    }

    return cfile;
}

/** Get a pointer to the file_desc_t using the ncid. */
int
pio_get_file_from_id2(int ncid, file_desc_t **cfile1)
{
    file_desc_t *cfile = NULL;

    LOG((2, "pio_get_file_from_id2 ncid = %d", ncid));

    /* Caller must provide this. */
    if (!cfile1)
	return PIO_EINVAL;

    /* Find the file pointer. */
    if (current_file && current_file->pio_ncid == ncid)
	cfile = current_file;
    else
	for (cfile = pio_file_list; cfile; cfile=cfile->next)
	{
	    if (cfile->pio_ncid == ncid)
	    {
		current_file = cfile;
		break;
	    }
	}

    /* If not found, return error. */
    if (!cfile)
	return PIO_EBADID;

    LOG((3, "file found!"));

    /* Copy pointer to file info. */
    *cfile1 = cfile;

    return PIO_NOERR;
}

/** Delete a file from the list of open files. */
int pio_delete_file_from_list(int ncid)
{

    file_desc_t *cfile, *pfile = NULL;

    /* Look through list of open files. */
    for (cfile = pio_file_list; cfile; cfile = cfile->next)
    {
	if (cfile->pio_ncid == ncid)
	{
	    if (!pfile)
		pio_file_list = cfile->next;
	    else
		pfile->next = cfile->next;

	    if (current_file == cfile)
		current_file = pfile;

	    /* Free the memory used for this file. */
	    free(cfile);
	    return PIO_NOERR;
	}
	pfile = cfile;
    }

    /* No file was found. */
    return PIO_EBADID;
}

/** Delete iosystem info from list. */
int pio_delete_iosystem_from_list(int piosysid)
{
    iosystem_desc_t *ciosystem, *piosystem;
    piosystem = NULL;

    for (ciosystem = pio_iosystem_list; ciosystem; ciosystem = ciosystem->next)
	LOG((2, "iosysid = %d union_comm = %d io_comm = %d my_comm = %d intercomm = %d comproot = %d"
	     " next = %d",
	     ciosystem->iosysid, ciosystem->union_comm, ciosystem->io_comm, ciosystem->my_comm,
	     ciosystem->intercomm, ciosystem->comproot, ciosystem->next));

    LOG((1, "pio_delete_iosystem_from_list piosysid = %d", piosysid));
    for (ciosystem = pio_iosystem_list; ciosystem; ciosystem = ciosystem->next)
    {
	LOG((3, "iosysid = %d union_comm = %d io_comm = %d my_comm = %d intercomm = %d comproot = %d",
	     ciosystem->iosysid, ciosystem->union_comm, ciosystem->io_comm, ciosystem->my_comm,
	     ciosystem->intercomm, ciosystem->comproot));
	if (ciosystem->iosysid == piosysid)
	{
	    if (piosystem == NULL)
	    {
		LOG((3, "start of list"));
		pio_iosystem_list = ciosystem->next;
	    }
	    else
	    {
		LOG((3, "setting next"));
		piosystem->next = ciosystem->next;
	    }
	    free(ciosystem);
	    return PIO_NOERR;
	}
	piosystem = ciosystem;
    }
    return PIO_EBADID;
}

int pio_add_to_iosystem_list(iosystem_desc_t *ios)
{
  iosystem_desc_t *cios;
  int i=1;

  //assert(ios != NULL);
  ios->next = NULL;
  cios = pio_iosystem_list;
  if(cios==NULL)
    pio_iosystem_list = ios;
  else{
    i++;
    while(cios->next != NULL){
      cios = cios->next;
      i++;
    }
    cios->next = ios;
  }
  ios->iosysid = i << 16;
  //  ios->iosysid = i ;
  //  printf(" ios = %ld %d %ld\n",ios, ios->iosysid,ios->next);
  return ios->iosysid;
}

iosystem_desc_t *pio_get_iosystem_from_id(int iosysid)
{
    iosystem_desc_t *ciosystem;

    LOG((2, "pio_get_iosystem_from_id iosysid = %d", iosysid));

    for (ciosystem = pio_iosystem_list; ciosystem; ciosystem = ciosystem->next)
	if (ciosystem->iosysid == iosysid)
	{
	    LOG((3, "FOUND! iosysid = %d union_comm = %d comp_comm = %d io_comm = %d my_comm = %d "
		 "intercomm = %d comproot = %d next = %d",
		 ciosystem->iosysid, ciosystem->union_comm, ciosystem->comp_comm, ciosystem->io_comm,
		 ciosystem->my_comm, ciosystem->intercomm, ciosystem->comproot, ciosystem->next));
	    return ciosystem;
	}


    return NULL;

}

int pio_add_to_iodesc_list(io_desc_t *iodesc)
{
  io_desc_t *ciodesc;
  int imax=512;

  iodesc->next = NULL;
  if(pio_iodesc_list == NULL)
    pio_iodesc_list = iodesc;
  else{
    imax++;
    for(ciodesc = pio_iodesc_list; ciodesc->next != NULL; ciodesc=ciodesc->next, imax=ciodesc->ioid+1);
    ciodesc->next = iodesc;
  }
  iodesc->ioid = imax;
  current_iodesc = iodesc;
  //  printf("In add to list %d\n",iodesc->ioid);
  return iodesc->ioid;
}


io_desc_t *pio_get_iodesc_from_id(int ioid)
{
  io_desc_t *ciodesc;

  ciodesc = NULL;

  if(current_iodesc != NULL && current_iodesc->ioid == abs(ioid))
    ciodesc=current_iodesc;
  for(ciodesc=pio_iodesc_list; ciodesc != NULL; ciodesc=ciodesc->next){
    if(ciodesc->ioid == abs(ioid)){
      current_iodesc = ciodesc;
      break;
    }
  }
  /*
  if(ciodesc==NULL){
    for(ciodesc=pio_iodesc_list; ciodesc != NULL; ciodesc=ciodesc->next){
      printf("%s %d %d %d\n",__FILE__,__LINE__,ioid,ciodesc->ioid);
    }
  }
  */

  return ciodesc;
}

int pio_delete_iodesc_from_list(int ioid)
{

  io_desc_t *ciodesc, *piodesc;

  piodesc = NULL;
  //  if(abs(ioid)==518) printf("In delete from list %d\n", ioid);
  for(ciodesc=pio_iodesc_list; ciodesc != NULL; ciodesc=ciodesc->next){
    if(ciodesc->ioid == ioid){
      if(piodesc == NULL){
	pio_iodesc_list = ciodesc->next;
      }else{
	piodesc->next = ciodesc->next;
      }
      if(current_iodesc==ciodesc)
	current_iodesc=pio_iodesc_list;
      brel(ciodesc);
      return PIO_NOERR;
    }
    piodesc = ciodesc;
  }
  return PIO_EBADID;
}
