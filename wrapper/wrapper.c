/* 
 # File: wrapper.c
 # Project: data-acquisition
 # Last Modified: 2021-8-2
 # Created Date: 2021-8-2
 # Copyright (c) 2021
 # Author: AHMA project (Univ Rennes, CNRS, Inria, IRISA)
 # Modified By: Duy-Phuc Pham (duy-phuc.pham@irisa.fr)
/****
  gcc wrapper.c -o wrapper -l pthread
 *****/
#include <stdlib.h>
#include <stdio.h>
#include <time.h>
#include <pthread.h>

pthread_t t;

void *thread(void *arg) 
{
	char *cmd = arg;
	system(cmd);
}

void microsleep(int microseconds)  
{
	long usec = microseconds % 1000000;
	struct timespec ts_sleep;
	ts_sleep.tv_sec = microseconds / 1000000;
	ts_sleep.tv_nsec = 1000 * usec;
	nanosleep(&ts_sleep, NULL);
}

int main(int argc, char *argv[]) 
{
	if (argc < 2) {
		printf("usage: %s cmd [duration] (us)\n", argv[0]);
		return 1;
	}

	char *cmd = argv[1];
	if (argc > 2) {
		pthread_create(&t, NULL, &thread, cmd);
		int duration = atoi(argv[2]);
		microsleep(duration);
		pthread_cancel(t);
	} else {
		system(cmd);
	}

	return 0;
}

