// SPDX-License-Identifier: GPL-3.0-or-later
// Presentation-only helpers for the pinned Calamares 3.4.2 widget wizard.
#pragma once

#include <QBoxLayout>
#include <QEvent>
#include <QLabel>
#include <QPainter>
#include <QPixmap>
#include <QWidget>

namespace Nascent
{
// The original image label reports the full raster as its size hint. Paint it
// inside a bounded viewport instead, without cropping or changing the asset.
class Artwork : public QLabel
{
public:
    explicit Artwork( QWidget* parent ) : QLabel( parent )
    {
        setSizePolicy( QSizePolicy::Expanding, QSizePolicy::Expanding );
        setMinimumSize( 0, 0 );
    }
    QSize sizeHint() const override { return QSize( 640, 360 ); }
    QSize minimumSizeHint() const override { return QSize( 0, 0 ); }
protected:
    void paintEvent( QPaintEvent* ) override
    {
        const QPixmap image = pixmap();
        if ( image.isNull() ) { return; }
        QSize target = image.size();
        target.scale( QSize( qMin( width(), 640 ), qMin( height(), 360 ) ), Qt::KeepAspectRatio );
        QRect area( QPoint( 0, 0 ), target );
        area.moveCenter( rect().center() );
        QPainter painter( this );
        painter.setRenderHint( QPainter::SmoothPixmapTransform );
        painter.drawPixmap( area, image );
    }
};

// Watch the actual window: VM resize and display scaling can happen after boot.
// No fixed page heights, no changes to focus order, jobs, or navigation state.
class Insets : public QObject
{
public:
    Insets( QWidget* window, QWidget* sidebar, QBoxLayout* content, QWidget* center, QWidget* navigation )
        : QObject( window ), m_window( window ), m_sidebar( sidebar ), m_content( content ), m_center( center ), m_navigation( navigation )
    {
        window->installEventFilter( this );
        update();
    }
protected:
    bool eventFilter( QObject* watched, QEvent* event ) override
    {
        if ( event->type() == QEvent::Resize || event->type() == QEvent::Show
             || event->type() == QEvent::FontChange ) { update(); }
        return QObject::eventFilter( watched, event );
    }
private:
    void update()
    {
        const bool compact = m_window->height() < 660;
        const int inset = m_window->width() >= 1100 ? 40 : ( m_window->width() >= 900 ? 28 : 20 );
        m_content->setContentsMargins( inset, compact ? 20 : 32, inset, 0 );
        if ( m_sidebar && m_sidebar->layout() )
        {
            m_sidebar->setFixedWidth( m_window->width() < 1000 ? 196 : 224 );
            m_sidebar->layout()->setContentsMargins( 16, compact ? 20 : 28, 16, compact ? 16 : 24 );
            m_sidebar->layout()->setSpacing( compact ? 12 : 24 );
        }
        const int columnWidth = qMin( 1080, qMax( 0, m_window->width()
            - ( m_sidebar ? m_sidebar->width() : 0 ) - 2 * inset ) );
        m_center->setFixedWidth( columnWidth );
        if ( m_navigation ) { m_navigation->setFixedWidth( columnWidth ); }
        if ( m_navigation && m_navigation->layout() )
        {
            m_navigation->layout()->setContentsMargins( 0, compact ? 12 : 20, 0, compact ? 16 : 24 );
            m_navigation->layout()->setSpacing( 12 );
        }
    }
    QWidget* m_window;
    QWidget* m_sidebar;
    QBoxLayout* m_content;
    QWidget* m_center;
    QWidget* m_navigation;
};
}
