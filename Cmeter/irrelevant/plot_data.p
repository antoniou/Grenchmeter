reset
set boxwidth 0.8 absolute
set style fill solid border -1
set style histogram rowstacked title  offset character 0, -1, -1 
set grid nopolar
set grid layerdefault  linetype 0 linewidth 1.000,  linetype 0 linewidth 1.000
set key tmargin center horizontal center reverse enhanced autotitles columnhead nobox
set datafile missing '-'
set style data histograms
set xlabel  offset character 0, -1, 0 font "" textcolor lt -2 norotate
set title "Number of Instances vs Resource Acquisition Time" 
set ylabel "Resource Acquisition Time (s)"
set xtics  nomirror offset character 0, 0, 0 rotate by 90
#set xtics nomirror rotate by 90
set term postscript enhanced color font "Arial,20"
set size 1.0,1.0
set output 'acquire.eps'
plot newhistogram "m1.small", 'C:\workspace\Ec2Benchmark\experiments\results\overall_acquire.dat' using 2:xtic(1) t '|SSH|' , '' u ($3-$2) t '|OAT|-|SSH|' ,\
newhistogram "m1.large", '' u 4:xtic(1) t '|SSH|', '' u ($5-$4)t '|OAT|-|SSH|' ,\
newhistogram "m1.xlarge", '' u 6:xtic(1) t '|SSH|', '' u ($7-$6) t '|OAT|-|SSH|' 
#newhistogram "c1.medium", '' u 8:xtic(1) t '|SSH|', '' u ($9-$8) t '|OAT|-|SSH|' ,\
#newhistogram "c1.xlarge", '' u 10:xtic(1) t '|SSH|', '' u ($11-$10) t '|OAT|-|SSH|'

