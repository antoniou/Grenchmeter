#include <stdio.h>

int main(int argc, char** argv)
{
    int i;
    
    printf("# File-type: text/wl-spec\n");
    printf("# File-version: 1.2\n\n");
    
    for (i = 1; i < argc; i++)
	printf("%s\t", argv[i]);
}
