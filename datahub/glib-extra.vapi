[CCode (cprefix = "G", lower_case_cprefix = "g_")]
namespace GLibExtra {
  [CCode (cname = "GLIB_CHECK_VERSION")]
  public static bool check_version (uint major, uint minor, uint micro);
}
