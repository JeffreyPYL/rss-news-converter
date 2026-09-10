from news_digest.domain.models import Topic

TOPIC_TITLES: dict[Topic, str] = {
    Topic.OTTAWA: "Ottawa",
    Topic.CANADA: "Canada",
    Topic.HONG_KONG: "Hong Kong",
    Topic.CHINA: "China",
    Topic.TECH: "Tech",
    Topic.GLOBAL: "Global",
}
