#include <Python.h>              /* Python as seen from C */
#include <arrayobject.h>
#include <math.h>
#include <stdio.h>               /* for debug output */

static PyObject *stack(PyObject *self, PyObject *args);

static PyMethodDef c_stackMethods[] = {
  {"stack",    /* name of func when called from Python */
   stack,      /* corresponding C function */
   METH_VARARGS},   /* ordinary (not keyword) arguments */
  {NULL, NULL}     /* required ending of the method table */
};

void initc_stack()
{
  /* Assign the name of the module and the name of the
     method table and (optionally) a module doc string:
  */
  Py_InitModule("c_stack", c_stackMethods);
  import_array();   /* required NumPy initialization */
}

static PyObject *stack(PyObject *self, PyObject *args)
{
  PyArrayObject *vecin1, *vecin2, *vecout;
  int nx, i;
  double *cin1, *cin2, *cout;

  /* arguments: a, xcoor, ycoor*/
  /* parsing without checking the pointer types: */
  if (!PyArg_ParseTuple(args, "O!O!O!", &PyArray_Type, &vecin1, &PyArray_Type, &vecin2, 
			&PyArray_Type, &vecout)) 
    { return NULL; }
  cin1 = (double *) vecin1->data;
  cin2 = (double *) vecin2->data;
  cout = (double *) vecout->data;
  nx = vecin1->dimensions[0];
  for (i=0; i<nx; i++) {
    cout[i] = cin1[i]+cin2[i];
  }
  return Py_BuildValue("i",1);  /* return 1 */
}


