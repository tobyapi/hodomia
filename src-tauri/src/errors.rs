pub(crate) fn message(error: impl std::fmt::Display) -> String {
    error.to_string()
}
