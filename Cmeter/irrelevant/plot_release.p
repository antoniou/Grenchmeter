reset
set border 3 front linetype -1 linewidth 1.000
set boxwidth 0.75 absolute
set style fill  solid 1.00 border -1
set style fill  solid 1.00 noborder


set grid noxtics nomxtics ytics nomytics noztics nomztics \
 nox2tics nomx2tics noy2tics nomy2tics nocbtics nomcbtics
set grid layerdefault   linetype 0 linewidth 1.000,  linetype 0 linewidth 1.000
set key bmargin center horizontal Left reverse enhanced autotitles columnhead nobox
set datafile missing '-'
set style data histograms
set title ""  
set ylabel "Resource Release Time [s]"
set xlabel  offset character 0, 0, 0 font "" textcolor lt -1 norotate "Number of Instances"
set term postscript enhanced color font "Arial,15"
set output 'release.eps'
set xtics nomirror
set ytics 10 nomirror
set yrange [0:40]
set mytics 5
#plot 'C:\workspace\Ec2Benchmark\experiments\results\overall_release.dat' using 6:xtic(1) t 'c1.xlarge',\
#'' u 5:xtic(1) t 'c1.medium',\
#'' u 4:xtic(1) t 'm1.xlarge',\
#'' u 3:xtic(1) t 'm1.large',\
#'' u 2:xtic(1) t 'm1.small'

plot 'C:\workspace\Ec2Benchmark\experiments\results\overall_release.dat'  using 4:xtic(1) t 'm1.xlarge',\
'' u 3:xtic(1) t 'm1.large',\
'' u 2:xtic(1) t 'm1.small'
