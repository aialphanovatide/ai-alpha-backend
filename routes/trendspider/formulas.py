
def add_0_25(last_price):
    try:
        last_price = float(last_price)
        result = last_price * 1.0025
        formatted_price = f'{result:.2f}'
        return formatted_price
    except Exception as e:
        print(f"An error occurred: {e}")
        return f"An error occurred: {e}"


def formulas_long(accuracy, entry_range, r_r_r, tp1, tp2, tp3, tp4, sl1, sl2):

    try:
        risk_return_ratio = float(r_r_r)
        accuracy = float(accuracy) 
        entry_range = float(entry_range)
        tp_1 = float(tp1.strip('%'))
        tp_2 = float(tp2.strip('%'))
        tp_3 = float(tp3.strip('%'))
        tp_3 = float(tp3.strip('%'))
        tp_4 = float(tp4.strip('%'))
        sl_1 = float(sl1.strip('%'))
        sl_2 = float(sl2.strip('%'))

        if 50 <= accuracy <= 69:

            TP_1 = entry_range + (entry_range * tp_1 / 100) 
            TP_2 = entry_range + (entry_range * tp_2 / 100)  
            TP_3 = entry_range + (entry_range * tp_3 / 100)  
            TP_4 = entry_range + (entry_range * tp_4 / 100)  
            stop_loss_1 = entry_range - (entry_range * sl_1 / 100) 
            stop_loss_2 = entry_range - (entry_range * sl_2 / 100) 
            
        
        elif 70 <= accuracy <= 74:

            TP_1 = entry_range + (entry_range * tp_1 / 100) 
            TP_2 = entry_range + (entry_range * tp_2 / 100)  
            TP_3 = entry_range + (entry_range * tp_3 / 100)  
            TP_4 = entry_range + (entry_range * tp_4 / 100)  
            stop_loss_1 = entry_range - (entry_range * sl_1 / 100) 
            stop_loss_2 = entry_range - (entry_range * sl_2 / 100) 

        elif 75 <= accuracy <= 79:

            TP_1 = entry_range + (entry_range * tp_1 / 100) 
            TP_2 = entry_range + (entry_range * tp_2 / 100)  
            TP_3 = entry_range + (entry_range * tp_3 / 100)  
            TP_4 = entry_range + (entry_range * tp_4 / 100)  
            stop_loss_1 = entry_range - (entry_range * sl_1 / 100) 
            stop_loss_2 = entry_range - (entry_range * sl_2 / 100) 

        elif 80 <= accuracy <= 84:
        
            TP_1 = entry_range + (entry_range * tp_1 / 100) 
            TP_2 = entry_range + (entry_range * tp_2 / 100)  
            TP_3 = entry_range + (entry_range * tp_3 / 100)  
            TP_4 = entry_range + (entry_range * tp_4 / 100)  
            stop_loss_1 = entry_range - (entry_range * sl_1 / 100) 
            stop_loss_2 = entry_range - (entry_range * sl_2 / 100) 

        elif 85 <= accuracy <= 89:

            TP_1 = entry_range + (entry_range * tp_1 / 100) 
            TP_2 = entry_range + (entry_range * tp_2 / 100)  
            TP_3 = entry_range + (entry_range * tp_3 / 100)  
            TP_4 = entry_range + (entry_range * tp_4 / 100)  
            stop_loss_1 = entry_range - (entry_range * sl_1 / 100) 
            stop_loss_2 = entry_range - (entry_range * sl_2 / 100) 

        elif 90 <= accuracy <= 94:

            TP_1 = entry_range + (entry_range * tp_1 / 100) 
            TP_2 = entry_range + (entry_range * tp_2 / 100)  
            TP_3 = entry_range + (entry_range * tp_3 / 100)  
            TP_4 = entry_range + (entry_range * tp_4 / 100)  
            stop_loss_1 = entry_range - (entry_range * sl_1 / 100) 
            stop_loss_2 = entry_range - (entry_range * sl_2 / 100) 

        elif 95 <= accuracy <= 99:

            TP_1 = entry_range + (entry_range * tp_1 / 100) 
            TP_2 = entry_range + (entry_range * tp_2 / 100)  
            TP_3 = entry_range + (entry_range * tp_3 / 100)  
            TP_4 = entry_range + (entry_range * tp_4 / 100)  
            stop_loss_1 = entry_range - (entry_range * sl_1 / 100) 
            stop_loss_2 = entry_range - (entry_range * sl_2 / 100) 

        else:
            return
        
        formatted_TP_1 = f'{TP_1:,.2f}'
        formatted_TP_2 = f'{TP_2:,.2f}'
        formatted_TP_3 = f'{TP_3:,.2f}'
        formatted_TP_4 = f'{TP_4:,.2f}'
        stop_loss_1 = f'{stop_loss_1:,.2f}'
        stop_loss_2 = f'{stop_loss_2:,.2f}'

        return formatted_TP_1, formatted_TP_2, formatted_TP_3, formatted_TP_4, stop_loss_1, stop_loss_2
    except Exception as e:
        print(f"An error occurred: {e}")


def formulas_short(accuracy, entry_range, r_r_r, tp1, tp2, tp3, tp4, sl1, sl2):

    try:

        risk_return_ratio = float(r_r_r)
        accuracy = float(accuracy) 
        entry_range = float(entry_range)
        tp_1 = float(tp1.strip('%'))
        tp_2 = float(tp2.strip('%'))
        tp_3 = float(tp3.strip('%'))
        tp_3 = float(tp3.strip('%'))
        tp_4 = float(tp4.strip('%'))
        sl_1 = float(sl1.strip('%'))
        sl_2 = float(sl2.strip('%'))   
    
        if 50 <= accuracy <= 69:

            TP_1 = entry_range - (entry_range * tp_1 / 100) 
            TP_2 = entry_range - (entry_range * tp_2 / 100)  
            TP_3 = entry_range - (entry_range * tp_3 / 100)  
            TP_4 = entry_range - (entry_range * tp_4 / 100)  
            stop_loss_1 = entry_range + (entry_range * sl_1 / 100) 
            stop_loss_2 = entry_range + (entry_range * sl_2 / 100) 
        
        elif 70 <= accuracy <= 74:

            TP_1 = entry_range - (entry_range * tp_1 / 100) 
            TP_2 = entry_range - (entry_range * tp_2 / 100)  
            TP_3 = entry_range - (entry_range * tp_3 / 100)  
            TP_4 = entry_range - (entry_range * tp_4 / 100)  
            stop_loss_1 = entry_range + (entry_range * sl_1 / 100) 
            stop_loss_2 = entry_range + (entry_range * sl_2 / 100) 

        elif 75 <= accuracy <= 79:

            TP_1 = entry_range - (entry_range * tp_1 / 100) 
            TP_2 = entry_range - (entry_range * tp_2 / 100)  
            TP_3 = entry_range - (entry_range * tp_3 / 100)  
            TP_4 = entry_range - (entry_range * tp_4 / 100)  
            stop_loss_1 = entry_range + (entry_range * sl_1 / 100) 
            stop_loss_2 = entry_range + (entry_range * sl_2 / 100) 

        elif 80 <= accuracy <= 84:
            
            TP_1 = entry_range - (entry_range * tp_1 / 100) 
            TP_2 = entry_range - (entry_range * tp_2 / 100)  
            TP_3 = entry_range - (entry_range * tp_3 / 100)  
            TP_4 = entry_range - (entry_range * tp_4 / 100)  
            stop_loss_1 = entry_range + (entry_range * sl_1 / 100) 
            stop_loss_2 = entry_range + (entry_range * sl_2 / 100) 

        elif 85 <= accuracy <= 89:

            TP_1 = entry_range - (entry_range * tp_1 / 100) 
            TP_2 = entry_range - (entry_range * tp_2 / 100)  
            TP_3 = entry_range - (entry_range * tp_3 / 100)  
            TP_4 = entry_range - (entry_range * tp_4 / 100)  
            stop_loss_1 = entry_range + (entry_range * sl_1 / 100) 
            stop_loss_2 = entry_range + (entry_range * sl_2 / 100) 

        elif 90 <= accuracy <= 94:

            TP_1 = entry_range - (entry_range * tp_1 / 100) 
            TP_2 = entry_range - (entry_range * tp_2 / 100)  
            TP_3 = entry_range - (entry_range * tp_3 / 100)  
            TP_4 = entry_range - (entry_range * tp_4 / 100)  
            stop_loss_1 = entry_range + (entry_range * sl_1 / 100) 
            stop_loss_2 = entry_range + (entry_range * sl_2 / 100) 

        elif 95 <= accuracy <= 99:

            TP_1 = entry_range - (entry_range * tp_1 / 100) 
            TP_2 = entry_range - (entry_range * tp_2 / 100)  
            TP_3 = entry_range - (entry_range * tp_3 / 100)  
            TP_4 = entry_range - (entry_range * tp_4 / 100)  
            stop_loss_1 = entry_range + (entry_range * sl_1 / 100) 
            stop_loss_2 = entry_range + (entry_range * sl_2 / 100) 

        else:
            return
        
        formatted_TP_1 = f'{TP_1:,.2f}'
        formatted_TP_2 = f'{TP_2:,.2f}'
        formatted_TP_3 = f'{TP_3:,.2f}'
        formatted_TP_4 = f'{TP_4:,.2f}'
        stop_loss_1 = f'{stop_loss_1:,.2f}'
        stop_loss_2 = f'{stop_loss_2:,.2f}'

        return formatted_TP_1, formatted_TP_2, formatted_TP_3, formatted_TP_4, stop_loss_1, stop_loss_2
    
    except Exception as e:
        print(f"An error occurred: {e}")