import pytest
from app.queue import rabbitmq

class DummyChannel:
    def __init__(self):
        self.declared = False
        self.published = False

    def queue_declare(self, queue, durable=True):
        self.declared = True

    def basic_publish(self, exchange, routing_key, body, properties):
        self.published = True

class DummyConnection:
    def __init__(self):
        self.channel_obj = DummyChannel()

    def channel(self):
        return self.channel_obj

    def close(self):
        pass


def test_publish_message_failure(monkeypatch):
    # Simulate connection error
    monkeypatch.setattr(rabbitmq, "get_rabbitmq_connection", lambda: (_ for _ in ()).throw(Exception("fail")))
    assert rabbitmq.publish_message("test", {"key": "value"}) is False


def test_publish_message_success(monkeypatch):
    # Simulate successful publish
    dummy_conn = DummyConnection()
    monkeypatch.setattr(rabbitmq, "get_rabbitmq_connection", lambda: dummy_conn)
    result = rabbitmq.publish_message("queue", {"foo": "bar"})
    assert result is True
    assert dummy_conn.channel_obj.declared
    assert dummy_conn.channel_obj.published
