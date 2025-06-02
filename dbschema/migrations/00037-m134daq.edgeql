CREATE MIGRATION m134daqcvzezm2zxmdi3fomwtpqboxhocl6lyxhprfjj46rludolxa
    ONTO m17b6yj57wsivjzkzj5gvyfji3v6nxgdf6h5pmsgowpavln3xxtecq
{
  ALTER TYPE discord::Message {
      ALTER PROPERTY content {
          SET REQUIRED USING (<std::str>std::json_get(.data, 'content'));
      };
  };
};
