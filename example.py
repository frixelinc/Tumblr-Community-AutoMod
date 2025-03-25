from AutoMod import Automod

automod = None
def main():
    global automod
    try:
        
        automod = Automod()
        logged_in = automod.get_login_cookie(True)
        if logged_in:
            automod.get_todays_posts()
            automod.start_automod_monitor()

    except Exception as e:
        print('Caught Exception: %s' % str(e))
        input('Program will now quit. (Enter) anything to continue: ')
        if automod is not None and isinstance(automod, Automod):
            automod.close_driver()


if __name__ == '__main__':
    main()

