import arcpy

def calc_average(file_list, avg_file):
#    print "calcAverage: ", file_list
    arcpy.cellSize = "MAXOF"
    arcpy.extent = "MAXOF"
    outRaster = arcpy.sa.CellStatistics(file_list, "MEAN")
    # Save the output
    outRaster.save(avg_file)
#    print "saved avg in: ", avg_file
    return None

def calc_min(file_list, min_file):
#    print "calcMin: ", file_list
    arcpy.cellSize = "MAXOF"
    arcpy.extent = "MAXOF"
    outRaster = arcpy.sa.CellStatistics(file_list, "MINIMUM")
    # Save the output
    outRaster.save(min_file)
#    print "saved minimum in: ", min_file
    return None

def calc_max(file_list, max_file):
#    print "calcAverage: ", file_list
    arcpy.cellSize = "MAXOF"
    arcpy.extent = "MAXOF"
    outRaster = arcpy.sa.CellStatistics(file_list, "MAXIMUM")
    # Save the output
    outRaster.save(max_file)
#    print "saved maximum in: ", max_file
    return None

def calc_std_dev(file_list, sd_file):
#    print "calcStDev: ", file_list
    arcpy.cellSize = "MAXOF"
    arcpy.extent = "MAXOF"
    outRaster = arcpy.sa.CellStatistics(file_list, "STD")
    # Save the output
    outRaster.save(sd_file)
#    print "saved standard deviation in: ", sd_file
    return None

def calc_sum(file_list, sum_file):
#    print "calcSum: ", file_list
    arcpy.cellSize = "MAXOF"
    arcpy.extent = "MAXOF"
    outRaster = arcpy.sa.CellStatistics(file_list, "SUM")
    # Save the output
    outRaster.save(sum_file)
#    print "saved sum in: ", sum_file
    return None

def calc_average_of_day_night(day_file, night_file, avg_file):
    print "calcAverage: ", day_file, night_file
    #an empty array/vector in which to store the different bands
    rasters = []
    #open rasters
    rasters.append(day_file)
    rasters.append(night_file)
    outRaster = arcpy.sa.CellStatistics(rasters, "MEAN", "DATA")
    # Save the output
    outRaster.save(avg_file)
    print "saved avg in: ", avg_file
    return None

def calc_zonal_statistics(raster_file, polygon_file, zone_field, output_table):
    # first calculate statistics on raster
    arcpy.CalculateStatistics_management(in_raster_dataset=raster_file)
    # now calculate zonal statistics as table
    arcpy.sa.ZonalStatisticsAsTable(in_zone_data=polygon_file, zone_field=zone_field,
                                    in_value_raster=raster_file,out_table=output_table)
    return None