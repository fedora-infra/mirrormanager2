import update_1_2_10
import update_1_3_2
import update_1_4_0

def update():
    """Fills newly created database columns with information.
    Run this after using tg-admin sql upgrade.
    """
    update_1_2_10.update()
    update_1_3_2.update()
    update_1_4_0.update()
