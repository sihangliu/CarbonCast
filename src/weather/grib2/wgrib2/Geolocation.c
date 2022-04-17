#include <stdio.h>
#include <stdlib.h>
#include <limits.h>
#include <math.h>
#include <string.h>
#include "grb2.h"
#include "wgrib2.h"
#include "fnlist.h"

/*
 * Geolocation.c
 *
 * 4/2020 Public Domain by Wesley Ebisuzaki
 *
 */


/*
 * HEADER:100:geolocation:inv:0:package (proj4,gctpc,internal,not_used) to get lat/lon of grid points
 */

extern enum geolocation_type geolocation;

int f_geolocation(ARG0) {

    if (mode >= 0) {
        if (geolocation == proj4) strcat(inv_out,"proj4");
        else if (geolocation == gctpc) strcat(inv_out,"gctpc");
        else if (geolocation == internal) strcat(inv_out,"internal");
        else if (geolocation == not_used) strcat(inv_out,"not_used");
    }
    return 0;
}
