import datetime


class UTC(datetime.tzinfo):
    """
    UTC is a concrete subclass of datetime.tzinfo representing the UTC
    time zone.
    """

    def utcoffset(self, dt):
        return datetime.timedelta(0)

    def tzname(self, dt):
        return "UTC"

    def dst(self, dt):
        return datetime.timedelta(0)


def make_utc_datetime_rfc3339():
    return (
        datetime.datetime.utcnow().replace(microsecond=0, tzinfo=UTC()).isoformat("T")
    )
