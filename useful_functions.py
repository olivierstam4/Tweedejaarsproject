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
    For Locus: sensor_type = 'locus'
    For Alta: sensor_type = 'alta'

    For sensor_number, use the one of the file, (B.253, etc)
    """
    import pandas as pd
    return pd.read_excel(f'Data_clean/{sensor_type}_sensors/{sensor_number}_processed.xlsx')