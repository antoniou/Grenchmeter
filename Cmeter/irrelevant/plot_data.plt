reset
set border 3 front linetype -1 linewidth 1.000
set boxwidth 0.75 absolute
set style fill  solid 1.00 border -1

set grid noxtics nomxtics ytics nomytics noztics nomztics \
 nox2tics nomx2tics noy2tics nomy2tics nocbtics nomcbtics
set grid layerdefault   linetype 0 linewidth 1.000,  linetype 0 linewidth 1.000

set key bmargin center horizontal Left reverse enhanced autotitles columnhead nobox

set style histogram rowstacked title  
 
set style data histograms 

set xlabel  offset character 0,0, 0 "Number of Instances"

set title "" 
set ylabel "Resource Acquisition Time [s]"

set xtics rotate 90 nomirror
set ytics nomirror
set mytics 5
set bmargin 9
set term postscript enhanced color font "Arial,14"
set size 1.0,1.0
set output 'acquire.eps'
plot newhistogram "m1.small", 'C:\workspace\Ec2Benchmark\experiments\results\overall_acquire.dat' using 2:xtic(1) t 'SSH            ', '' u ($3-$2) t 'OAT-SSH            ' ,\
newhistogram "m1.large", '' u 4:xtic(1) t 'SSH            ', '' u ($5-$4)t 'OAT-SSH            ' ,\
newhistogram "m1.xlarge", '' u 6:xtic(1) t 'SSH            ', '' u ($7-$6) t 'OAT-SSH            ' 
#newhistogram "c1.medium", '' u 8:xtic(1) t '|SSH|', '' u ($9-$8) t '|OAT|-|SSH|' ,\
#newhistogram "c1.xlarge", '' u 10:xtic(1) t '|SSH|', '' u ($11-$10) t '|OAT|-|SSH|'
