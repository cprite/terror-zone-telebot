import datetime
import os


def set_advert(text, days):

    start_date = datetime.datetime.now()
    end_date = start_date + datetime.timedelta(days=days)

    with open(os.path.join("app/admin/commercial", "ads.txt"), 'w') as f:
        f.write(f'{text}\n{start_date}\n{end_date}')


def get_advert():
    try:
        with open(os.path.join("app/admin/commercial", "ads.txt"), 'r') as f:
            ads = f.readlines()

            text = "\n".join(ads[:-2])
            start_date = datetime.datetime.strptime(ads[-2].strip(), '%Y-%m-%d %H:%M:%S.%f')
            end_date = datetime.datetime.strptime(ads[-1].strip(), '%Y-%m-%d %H:%M:%S.%f')
    except:
        return None

    if not text:
        return None

    today = datetime.datetime.now()

    if start_date <= today <= end_date:
        return text
    elif today > end_date:
        with open(os.path.join("app/admin/commercial", "ads.txt"), 'w') as f:
            f.write('')
        return None


def delete_advert():
    with open(os.path.join("app/admin/commercial", "ads.txt"), 'w') as f:
        f.write('')


def advert_isActive():
    return bool(get_advert())
