/****************************************************************************
**
** This file is part of the LibreCAD project, a 2D CAD program
**
** Copyright (C) 2011 R. van Twisk (librecad@rvt.dds.nl)
** Copyright (C) 2011 Rallaz (rallazz@gmail.com)
**
** This file is free software; you can redistribute it and/or modify
** it under the terms of the GNU General Public License as published by
** the Free Software Foundation; either version 2 of the License, or
** (at your option) any later version.
**
****************************************************************************/

#ifndef QC_PLUGININTERFACE_H
#define QC_PLUGININTERFACE_H

#include <QtPlugin>

class Document_Interface;

class PluginMenuLocation {
public:
    PluginMenuLocation(QString menuEntryPoint, QString menuEntryActionName, QString menuEntryAction_Tip) {
        this->menuEntryAction_Tip = menuEntryAction_Tip;
        this->menuEntryActionName = menuEntryActionName;
        this->menuEntryPoint = menuEntryPoint;
    }

    QString menuEntryPoint;
    QString menuEntryActionName;
    QString menuEntryAction_Tip;
};

class PluginCapabilities {
public:
    QList<PluginMenuLocation> menuEntryPoints;
    QList<int> paintEventPriorities;
};

class QC_PluginInterface {
public:
    virtual ~QC_PluginInterface() {}
    virtual QString name() const = 0;
    virtual PluginCapabilities getCapabilities() const = 0;
    virtual void execComm(Document_Interface *doc, QWidget *parent, QString cmd) = 0;
};

#define LC_DocumentInterface_iid "org.librecad.PluginInterface/1.0"
Q_DECLARE_INTERFACE(QC_PluginInterface, LC_DocumentInterface_iid)

#endif

