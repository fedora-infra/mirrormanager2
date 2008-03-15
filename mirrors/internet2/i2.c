/* Quick & dirty program to parse (Internet2) BGP tables and check
 * whether an IP is in any of the netblocks
 * 
 * To use it, run the zebra-dump-parser tool [1] on a RIB table, direct
 * its output to 'rl.txt', then
 *
 * $ ./i2      # creates a table.bin file
 * # > Loaded N routes.
 * $ echo 128.8.5.2 | ./i2 check
 * # > PASS
 * $ echo 127.0.0.1 | ./i2 check
 * # > FAIL
 *
 * [1] http://www.linux.it/~md/software/zebra-dump-parser.tgz
 *
 * Copyright 2008 Ken Tossell <ken@tossell.net>
 *
 * Permission to use, copy, modify and/or distribute this software
 * for any purpose, with or without fee, is hereby granted. This
 * software is provided "as is." There is no warranty of fitness
 * or otherwise; the author will not be held liable for any
 * damages involving this software.
 *
 */

#include <stdio.h>
#include <stdlib.h>

struct CIDR {
	unsigned int prefix;
	unsigned char mask;
};

struct Map {
	unsigned int length;
	unsigned int capacity;
	struct CIDR *cidrs;
};

int load_text (struct Map *map) {
	char line[100] = {0};
	FILE *fp;
	unsigned int prefix[4];
	int mask;

	map->length = 0;
	map->capacity = 1024;
	map->cidrs = malloc(sizeof(struct CIDR) * map->capacity);

	if (!(fp = fopen("rl.txt", "r"))) {
		return 0;
	}

	while (fgets(line, 100, fp) != NULL) {	
		if (map->length == map->capacity) {
			map->capacity *= 2;
			map->cidrs = realloc(map->cidrs, sizeof(struct CIDR) * map->capacity);
		}

		
		if (sscanf(line, "%d.%d.%d.%d/%d", &prefix[0], &prefix[1], &prefix[2], &prefix[3], &mask) == 5) {
			map->cidrs[map->length].prefix = (prefix[0] << 24) | (prefix[1] << 16) | (prefix[2] << 8) | prefix[3];
			map->cidrs[map->length].mask = mask;
			map->length++;
		} else {
			printf("INVALID LINE: %s", line);
		}
	}

	return map->length;
}

inline void print_binary (unsigned int num) {
	int i;
	for (i = sizeof(unsigned int) * 8 - 1; i >= 0; --i) {
		putc(num & (1 << i) ? '1' : '0', stdout);
	}
	putc('\n', stdout);
}

void print_masks (struct Map *map) {
	int i;
	for (i = 0; i < map->length; ++i) {
		print_binary(map->cidrs[i].prefix);
	}
}

void check_ip (struct Map *map) {
	unsigned int ip;
	unsigned char bytes[4] = {0};
	scanf("%d.%d.%d.%d", &bytes[0], &bytes[1], &bytes[2], &bytes[3]);
	ip = (bytes[0] << 24) | (bytes[1] << 16) | (bytes[2] << 8) | bytes[3];

	int left = 0, test, right = map->length - 1;
	char found = 0;

	unsigned int ptr;
	// printf("%d.%d.%d.%d\n", *(ptr), *(ptr + 1), *(ptr + 2), *(ptr + 3));
	if (right >= 0) {
		do {
			test = (left + right) / 2;
			
			/* ptr = map->cidrs[test].prefix;
			printf("%u.%u.%u.%u/%u\n", ptr >> 24, (ptr >> 16) & 0xff, (ptr >> 8) & 0xff, (ptr & 0xff), map->cidrs[test].mask); */

			if ((map->cidrs[test].prefix >> (32 - map->cidrs[test].mask)) == (ip >> (32 - map->cidrs[test].mask))) {
				found = 1;
				
			} else if (ip > map->cidrs[test].prefix) {
				left = test + 1;
			} else {
				right = test;
			}
		} while (!found && left < right);
	}

	if (found) {
		printf("PASS\n");
	} else {
		printf("FAIL\n");
	}
}

void exp_tbl (struct Map *map) {
	FILE *fp = fopen("table.bin", "wb");

	fwrite(&map->length, sizeof(unsigned int), 1, fp);

	fwrite(map->cidrs, sizeof(struct CIDR), map->length, fp);

	fclose(fp);
}

int imp_tbl (struct Map *map) {
        FILE *fp = fopen("table.bin", "rb");

        if (!fp) return 0;

        if (!fread(&map->length, sizeof(unsigned int), 1, fp)) return 0;

        if (!(map->cidrs = malloc(sizeof(struct CIDR) * map->length))) {
                map->length = 0;
                return 0;
        }

        map->capacity = map->length;
        
        if (fread(map->cidrs, sizeof(struct CIDR), map->length, fp) != map->length) {
                return 0;
        }

        return map->capacity;
}

int main (int argc, char **argv) {
	struct Map map;

	if (argc == 1) {	
		if (load_text(&map)) {
			printf("%d routes loaded.\n", map.length);
			/* print_masks(&map); */
			exp_tbl(&map);
		} else {
			printf("No routes loaded.\n");
		}
	} else {
		if (imp_tbl(&map)) {
			check_ip(&map);
		} else {
			printf("FAIL\n");
		}
	}	

	return 0;
}
