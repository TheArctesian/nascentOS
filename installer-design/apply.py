#!/usr/bin/env python3
"""Apply a presentation-only adapter to Calamares 3.4.2; fail on source drift."""
from pathlib import Path
import sys


def apply(root, helper=None):
    here = Path(__file__).resolve().parent
    helper = helper or here / 'NascentLayout.h'
    helper_source = Path(helper).read_text()
    edits = {}

    def replace(name, before, after):
        source = edits.get(name, (root / name).read_text())
        if source.count(before) != 1:
            raise ValueError(f'{name}: expected exactly one anchor: {before!r}')
        edits[name] = source.replace(before, after, 1)

    window = 'src/calamares/CalamaresWindow.cpp'
    replace(window, '#include "CalamaresWindow.h"', '#include "CalamaresWindow.h"\n#include "NascentLayout.h"')
    replace(window, 'logoLabel->setFixedSize( 80, 80 );', 'logoLabel->setFixedSize( 56, 56 );')
    replace(window, '    ProgressTreeView* tv = new ProgressTreeView( sideBox );', '''    QLabel* productName = new QLabel( branding->productName(), sideBox );
    productName->setObjectName( "nascentProductName" );
    productName->setAlignment( Qt::AlignCenter );
    sideLayout->addWidget( productName );

    ProgressTreeView* tv = new ProgressTreeView( sideBox );''')
    replace(window, '    contentsLayout->addWidget( m_viewManager->centralWidget() );', '''    m_viewManager->centralWidget()->setMaximumWidth( 1080 );
    contentsLayout->addWidget( m_viewManager->centralWidget(), 1, Qt::AlignHCenter );
    if ( navigation ) { navigation->setMaximumWidth( 1080 ); }''')
    # Both widgets share the same centered, bounded content column.
    replace(window, '    insertIf( contentsLayout, PanelSide::Bottom, navigation, branding->navigationSide() );', '''    insertIf( contentsLayout, PanelSide::Bottom, navigation, branding->navigationSide() );
    if ( navigation ) { contentsLayout->setAlignment( navigation, Qt::AlignHCenter ); }''')
    replace(window, '    mainLayout->addLayout( contentsLayout );', '    mainLayout->addLayout( contentsLayout, 1 );')
    replace(window, '    setStyleSheet( Calamares::Branding::instance()->stylesheet() );',
            '    qApp->setStyleSheet( Calamares::Branding::instance()->stylesheet() );')
    replace(window, '    baseWidget->setLayout( mainLayout );', '''    baseWidget->setLayout( mainLayout );
    new Nascent::Insets( this, sideBox, contentsLayout, m_viewManager->centralWidget(), navigation );''')

    manager = 'src/libcalamaresui/ViewManager.cpp'
    replace(manager, '            const auto margins = step->widgetMargins( m_panelSides );', '''            // The outer content column owns the page inset, consistently across
            // modules (including ExecutionViewStep, which requests zero margins).
            const QSize margins( 0, 0 );''')

    delegate = 'src/calamares/progresstree/ProgressTreeDelegate.cpp'
    replace(delegate, 'static constexpr int const item_margin = 8;', 'static constexpr int const item_margin = 10;')
    replace(delegate, 'return Calamares::defaultFontSize() + 4;', 'return Calamares::defaultFontSize();')
    replace(delegate, 'font.setBold( false );', 'font.setBold( index.row() == index.data( Calamares::ViewManager::ProgressTreeItemCurrentIndex ).toInt() );')
    replace(delegate, '        painter->fillRect( option.rect, painter->brush().color() );', '''        painter->setPen( Qt::NoPen );
        painter->drawRoundedRect( option.rect.adjusted( 0, 2, 0, -2 ), 6, 6 );
        painter->setPen( QColor( Calamares::Branding::instance()->styleString(
            index.row() == index.data( Calamares::ViewManager::ProgressTreeItemCurrentIndex ).toInt()
                ? Calamares::Branding::SidebarTextCurrent : Calamares::Branding::SidebarText ) ) );''')
    replace(delegate, 'Qt::AlignHCenter | Qt::AlignVCenter | Qt::TextSingleLine', 'Qt::AlignLeft | Qt::AlignVCenter | Qt::TextSingleLine')

    tree = 'src/calamares/progresstree/ProgressTreeView.cpp'
    replace(tree, '    setContentsMargins( 0, 0, 0, 0 );', '''    setContentsMargins( 0, 0, 0, 0 );
    setHorizontalScrollBarPolicy( Qt::ScrollBarAlwaysOff );''')

    slides = 'src/libcalamaresui/viewpages/Slideshow.cpp'
    replace(slides, '#include "Slideshow.h"', '#include "Slideshow.h"\n#include "NascentLayout.h"')
    replace(slides, ', m_label( new QLabel( parent ) )', ', m_label( new Nascent::Artwork( parent ) )')

    execution = 'src/libcalamaresui/viewpages/ExecutionViewStep.cpp'
    replace(execution, '    m_progressBar->setMaximum( 10000 );', '''    auto* heading = new QLabel( tr( "Installing %1" ).arg( Branding::instance()->productName() ), m_widget );
    heading->setObjectName( "nascentPageTitle" );
    heading->setWordWrap( true );
    layout->addWidget( heading );
    bottomLayout->setSpacing( 10 );
    barLayout->setSpacing( 12 );
    m_label->setWordWrap( true );
    m_tab_widget->setObjectName( "nascentExecutionTabs" );
    m_progressBar->setTextVisible( false );
    auto* progressValue = new QLabel( m_widget );
    progressValue->setObjectName( "nascentProgressValue" );
    progressValue->setAlignment( Qt::AlignRight | Qt::AlignVCenter );
    connect( m_progressBar, &QProgressBar::valueChanged, progressValue,
             [this, progressValue]( int ) { progressValue->setText( m_progressBar->text() ); } );
    progressValue->setText( m_progressBar->text() );
    m_progressBar->setMaximum( 10000 );
    m_progressBar->setValue( 0 );''')
    replace(execution, '    Calamares::unmarginLayout( layout );', '''    Calamares::unmarginLayout( layout );
    layout->setSpacing( 24 );''')
    replace(execution, '    bottomLayout->addSpacing( Calamares::defaultFontHeight() / 2 );', '    // Outer column and row spacing own the breathing room.')
    replace(execution, '    QToolBar* toolBar = new QToolBar;', '''    QToolBar* toolBar = new QToolBar;
    toolBar->setObjectName( "nascentLogToolbar" );''')
    replace(execution, '    barLayout->addWidget( m_progressBar );', '''    barLayout->addWidget( m_progressBar, 1 );
    barLayout->addWidget( progressValue );''')
    replace(execution, '    connect( toggleLogButton, &QToolButton::clicked, this, &ExecutionViewStep::toggleLog );', '''    toggleLogButton->setAccessibleName( tr( "Show installation log" ) );
    toggleLogButton->setToolTip( tr( "Show installation log" ) );
    connect( toggleLogButton, &QToolButton::clicked, this, &ExecutionViewStep::toggleLog );''')

    # Validate all anchors before writing any file.
    for name, source in edits.items():
        (root / name).write_text(source)
    (root / 'src/libcalamaresui/NascentLayout.h').write_text(helper_source)


if __name__ == '__main__':
    apply(Path(sys.argv[1]), Path(sys.argv[2]) if len(sys.argv) > 2 else None)
