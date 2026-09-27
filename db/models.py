from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

class OpenTickets(Base):
    __tablename__ = 'open_tickets'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    panel_id = Column(Integer, ForeignKey('ticket_panels.id'), nullable=False)

class TicketPanels(Base):
    __tablename__ = 'ticket_panels'

    message_id = Column(Integer, primary_key=True)
    channel_id = Column(Integer, nullable=False)