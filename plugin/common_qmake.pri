# Shared qmake settings for local LibreCAD plugin builds.
#
# Keep this minimal and avoid forcing compilers or global flags so the
# selected Qt kit (msvc2019_64) controls ABI compatibility.

isEmpty(GENERATED_DIR) {
    GENERATED_DIR = ../../generated/plugin
}

OBJECTS_DIR = $${GENERATED_DIR}/obj
MOC_DIR = $${GENERATED_DIR}/moc
RCC_DIR = $${GENERATED_DIR}/rcc
UI_DIR = $${GENERATED_DIR}/ui

