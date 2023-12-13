for fw_bw in "FW" "BW"
do
    for day in {01..30}
    do
        for hour in {00..23}
        do
            wget "https://opendap.hereon.de/opendap/data/cosyna/synopsis/synopsis_${fw_bw}/${fw_bw}_2013_06/synop_201306${day}${hour}.nc"
        done
    done
done
