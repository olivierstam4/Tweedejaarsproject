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

# This function imports the right file
def import_file(sensor_type, sensor_number):
    """
    For Locus: sensor_type = 'locus', for the sensor number, only use the number (so not B),
    For Alta: sensor_type = 'alta', for the sensor number, do use the letter to, so use the entire first part of the filename
    """
    import pandas as pd
    if sensor_type == 'locus' :
        return pd.read_excel(f'Data_clean/{sensor_type}_sensors/2.B{sensor_number}_processed.xlsx')
    elif sensor_type == 'alta':
        return pd.read_excel(f'Data_clean/{sensor_type}_sensors/{sensor_number}_processed.xlsx')