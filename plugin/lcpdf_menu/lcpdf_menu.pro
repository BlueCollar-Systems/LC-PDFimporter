QT += widgets
TEMPLATE = lib
CONFIG += plugin c++17
TARGET = $$qtLibraryTarget(bc_lcpdf_menu)
VERSION = 1.0.0

GENERATED_DIR = ../../generated/plugin/lcpdf_menu
include(../common_qmake.pri)

INCLUDEPATH += ../sdk

SOURCES += lcpdf_menu.cpp
HEADERS += lcpdf_menu.h
