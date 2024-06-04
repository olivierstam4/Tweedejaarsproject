def remove_zeros(df):
    """
    Function for removing all zero values
    """
    df = df[df['Count'] > 0]
    return df

def remove_before(df, min_number):
    """
    Only keeps count values higher than min_number
    Can be used instead of remove_zeros
    """
    df = df[df['Count'] > min_number]
    return df

def import_file(sensor_type, sensor_number):
    """
    For Locus: sensor_type = 'Locus'
    For Alta: sensor_type = 'Alta'

    For sensor_number, use the one of the file, (B.253, etc)
    """
    import pandas as pd
    import os
    file_path = f'Data_clean/{sensor_type}_sensors/{sensor_number}_processed.xlsx'
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(
            f"Sensor_type moet met een hoofdletter beginnen!.\n"
            f"Voor sensor_number, kijk naar hoe de file heet en gebruik daarvan dus de eerste 4 karakters'\n"
            f"Examples: 'Data_clean/Locus_sensors/B.253_processed.xlsx', 'Data_clean/Alta_sensors/B.254_processed.xlsx'"
        )
    
    return pd.read_excel(file_path)