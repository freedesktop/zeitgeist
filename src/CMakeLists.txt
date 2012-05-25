set(engine_VALA_SRCS
  datamodel.vala
  db-reader.vala
  engine.vala
  remote.vala
  extension.vala
  extension-collection.vala
  extension-store.vala
  logging.vala
  notify.vala
  sql.vala
  utils.vala
  errors.vala
  table-lookup.vala
  sql-schema.vala
  where-clause.vala
  ontology.vala
  ontology-uris.vala
  mimetype.vala
  zeitgeist-daemon.vala
)

configure_file(${CMAKE_CURRENT_SOURCE_DIR}/config.vala.in ${CMAKE_CURRENT_BINARY_DIR}/config.vala)
vala_precompile(config_SRCS
  "${CMAKE_CURRENT_BINARY_DIR}/config.vala"
GENERATE_VAPI
  ${CMAKE_CURRENT_BINARY_DIR}/config.vapi
GENERATE_HEADER
  ${CMAKE_CURRENT_BINARY_DIR}/config.h
)

add_library(config STATIC ${config_SRCS})

vala_precompile(engine_SRCS
  ${engine_VALA_SRCS}
PACKAGES
  gio-2.0
  sqlite3
  posix
  gmodule-2.0
OPTIONS
  --target-glib=2.26
GENERATE_VAPI
  ${CMAKE_CURRENT_BINARY_DIR}/zeitgeist-engine.vapi
CUSTOM_VAPIS
  ${CMAKE_CURRENT_BINARY_DIR}/config.vapi
)

include_directories(
  ${GLIB2_INCLUDE_DIR}
  ${GOBJECT_INCLUDE_DIR}
  ${CMAKE_CURRENT_BINARY_DIR}
)

add_executable(zeitgeist-daemon ${engine_SRCS})

target_link_libraries(zeitgeist-daemon
  ${GLIB2_LIBRARIES}
  ${GOBJECT_LIBRARIES}
  ${SQLITE_LIBRARIES}
  ${GIO_LIBRARIES}
  config
)
